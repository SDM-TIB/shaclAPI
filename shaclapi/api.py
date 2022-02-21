import os, logging, time, json, re

from shaclapi.query import Query
from shaclapi.config import Config
from shaclapi.multiprocessing.functions import mp_validate, mp_xjoin, mp_post_processing, mp_output_completion
from shaclapi.multiprocessing.runner import Runner
from shaclapi.multiprocessing.contactSource import contactSource
from shaclapi.reduction.ValidationResultTransmitter import ValidationResultTransmitter
from shaclapi.statsCalculation import StatsCalculation
from shaclapi.output import Output

logger = logging.getLogger(__name__)

# This seems to load some pyparsing stuff and will speed up the execution of the first task by 1 second.
query = Query.prepare_query("PREFIX test1:<http://example.org/testGraph1#>\nSELECT DISTINCT ?x WHERE {\n?x a test1:classE.\n?x test1:has ?lit.\n}")
query.namespace_manager.namespaces()

# Building Multiprocessing Chain using Runners and Queries
# Validation ––> \              
#                 XJoin ––> PostProcessing ––> Output Generation
# Query      ––> /

# Dataprocessing Queues/Pipes --> 'EOF' is written by the runner class after function to execute finished

# Name                      | Sender - Threads          | Receiver - Threads        | Queue/Pipe    | Description
# ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
# val_queue                 | VALIDATION_RUNNER         | XJOIN_RUNNER              | Pipe          | Queue with validation results
# transformed_query_queue   | CONTACT_SOURCE_RUNNER     | XJOIN_RUNNER              | Pipe          | Query results in a joinable format 
# joined_results_queue      | XJOIN_RUNNER              | POST_PROCESSING_RUNNER    | Pipe          | Joined results (literals/non-shape uris missing, and still need to collect bindings with similar id)
# final_result_queue        | POST_PROCESSING_RUNNER    | OUTPUT_COMPLETION_RUNNER  | Pipe          | Collected results
# result_queue              | OUTPUT_COMPLETION_RUNNER  | -                         | Pipe          | Formatted results

# Queues to collect statistics: --> {"topic":...., "":....}
# stats_out_queue           | ALL_RUNNER                | Main Thread               | Queue         | one time statistics per run --> known number of statistics (also contains exception notifications in case a runner catches an exception)
# timestamp_queue           | POST_PROCESSING_RUNNER    | Main Thread               | Pipe          | variable number of result timestamps per run --> close with 'EOF' by queue_output_to_table

VALIDATION_RUNNER = Runner(mp_validate, number_of_out_queues=1)
CONTACT_SOURCE_RUNNER = Runner(contactSource, number_of_out_queues=1)
XJOIN_RUNNER = Runner(mp_xjoin, number_of_out_queues=1)
POST_PROCESSING_RUNNER = Runner(mp_post_processing, number_of_out_queues=2)
OUTPUT_COMPLETION_RUNNER = Runner(mp_output_completion, number_of_out_queues=1)

# Starting the processes of the runners
VALIDATION_RUNNER.start_process()
CONTACT_SOURCE_RUNNER.start_process()
XJOIN_RUNNER.start_process()
POST_PROCESSING_RUNNER.start_process()
OUTPUT_COMPLETION_RUNNER.start_process()

def get_result_queue():
    return OUTPUT_COMPLETION_RUNNER.get_new_out_queues(use_pipes=False)[0]

def run_multiprocessing(pre_config, result_queue = None):
    # Parse Config from POST Request and Config File
    config = Config.from_request_form(pre_config)
    logger.info("To reproduce this call to the api run: run_config.py -c '" +  json.dumps(config.config_dict) + "'")
    print("Name: " + __name__)
    os.makedirs(os.path.abspath(config.output_directory), exist_ok=True)
    os.makedirs(os.path.join(config.output_directory, config.backend, re.sub('[^\w\-_\. ]', '_', config.test_identifier)), exist_ok=True)


    # Setup Stats Calculation
    statsCalc = StatsCalculation(test_identifier = config.test_identifier, approach_name = os.path.basename(config.config))
    statsCalc.globalCalculationStart()

    # Setup Multiprocessing Queues
    if result_queue != None:
        QUEUE_OUTPUT = True
    else:
        result_queue = OUTPUT_COMPLETION_RUNNER.get_new_out_queues(config.use_pipes)[0]
        QUEUE_OUTPUT = False

    # 1.) Get Queues
    stats_out_queue = CONTACT_SOURCE_RUNNER.get_new_queue()
    contact_source_out_queues = CONTACT_SOURCE_RUNNER.get_new_out_queues(config.use_pipes) 
    validation_out_queues = VALIDATION_RUNNER.get_new_out_queues(config.use_pipes)
    xjoin_out_queues = XJOIN_RUNNER.get_new_out_queues(config.use_pipes)
    post_processing_out_queues = POST_PROCESSING_RUNNER.get_new_out_queues(config.use_pipes)
    output_completion_out_queues = (result_queue, )

    # 2.) Extract Out Queues
    transformed_query_queue = contact_source_out_queues[0] # pylint: disable=unbalanced-tuple-unpacking
    val_queue = validation_out_queues[0] # pylint: disable=unbalanced-tuple-unpacking
    joined_results_queue = xjoin_out_queues[0]
    final_result_queue, timestamp_queue = post_processing_out_queues # pylint: disable=unbalanced-tuple-unpacking

    # 3.) Zip Out Connections
    contact_source_out_connections = tuple((queue_adapter.sender for queue_adapter in contact_source_out_queues))
    validation_out_connections = tuple((queue_adapter.sender for queue_adapter in validation_out_queues))
    xjoin_out_connections = tuple((queue_adapter.sender for queue_adapter in xjoin_out_queues))
    post_processing_out_connections = tuple((queue_adapter.sender for queue_adapter in post_processing_out_queues))
    output_completion_out_connections = tuple((queue_adapter.sender for queue_adapter in output_completion_out_queues))

    # 3.) Zip In Connections
    contact_source_in_connections = tuple()
    validation_in_connections = tuple()
    xjoin_in_connections = (transformed_query_queue.receiver, val_queue.receiver)
    post_processing_in_connections = (joined_results_queue.receiver, )
    output_completion_in_connections = (final_result_queue.receiver, )

    # Setup of the Validation Result Transmitting Strategie (Backend --> API)
    result_transmitter = ValidationResultTransmitter(output_queue=val_queue.sender, first_val_time_queue=stats_out_queue)

    # Parse query_string into a corresponding Query Object
    query = Query.prepare_query(config.query)
    query_starshaped = query.make_starshaped()

    collect_all_validation_results = config.collect_all_validation_results

    # Check if we got a non starshaped query
    if query_starshaped == None or config.target_shape == None:
        if collect_all_validation_results == False:
            collect_all_validation_results = True
            logger.warning('Running in blocking mode as the target variable or the target shape could not be identified!')
        if config.replace_target_query == True:
            config.config_dict['replace_target_query'] = False
            logger.warning('Can only replace target query if target shape is given and query is starshaped!')
        if config.prune_shape_network == True:
            config.config_dict['prune_shape_network'] = False
            logger.warning('Can only prune shape schema if target shape is given and query is starshaped!')
        if config.start_with_target_shape == True:
            config.config_dict['start_with_target_shape'] = False
            logger.warning('Can only start with target shape if target shape is given and query is starshaped!')
    else:
        query = query_starshaped

    # The information we need depends on the output format:
    if config.output_format == "test" or (not config.reasoning):
        query_to_be_executed = query.copy()
    else:
        query_to_be_executed = query.as_result_query()

    statsCalc.taskCalculationStart()

    # Start Processing Pipeline
    # 1.) Get the Data
    contact_source_task_description = (config.external_endpoint, query_to_be_executed.query_string, -1)
    CONTACT_SOURCE_RUNNER.new_task(contact_source_in_connections, contact_source_out_connections, contact_source_task_description, stats_out_queue, config.run_in_serial)

    validation_task_description = (config, query_to_be_executed.copy(), result_transmitter)
    VALIDATION_RUNNER.new_task(validation_in_connections, validation_out_connections, validation_task_description, stats_out_queue, config.run_in_serial)
    
    # 2.) Join the Data
    xjoin_task_description = (config,)
    XJOIN_RUNNER.new_task(xjoin_in_connections, xjoin_out_connections, xjoin_task_description, stats_out_queue, config.run_in_serial)

    # 3.) Post-Processing: Restore missing vars (these one which could not find a join partner (literals etc.))
    post_processing_task_description = (query_to_be_executed.PV, config.target_shape, query_to_be_executed.target_var, collect_all_validation_results)
    POST_PROCESSING_RUNNER.new_task(post_processing_in_connections, post_processing_out_connections, post_processing_task_description, stats_out_queue, config.run_in_serial)

    # 4.) Transform to Outputformat
    output_completion_task_description = (query.copy(),config.target_shape, config.output_format == 'test')
    OUTPUT_COMPLETION_RUNNER.new_task(output_completion_in_connections, output_completion_out_connections, output_completion_task_description, stats_out_queue, config.run_in_serial)

    if config.write_stats:
        matrix_file = os.path.join(os.path.abspath(config.output_directory), "matrix.csv")
        trace_file = os.path.join(os.path.abspath(config.output_directory), "trace.csv")
        stats_file = os.path.join(os.path.abspath(config.output_directory), "stats.csv")
    else:
        matrix_file = None
        trace_file = None
        stats_file = None

    try:
        statsCalc.receive_and_write_trace(trace_file, timestamp_queue.receiver)
        statsCalc.receive_global_stats(stats_out_queue, using_output_completion_runner=True)
        statsCalc.write_matrix_and_stats_files(matrix_file, stats_file)
    except Exception as e:
        logger.exception(repr(e))
        result_queue.sender.put('EOF')

    if QUEUE_OUTPUT == False:
        if config.output_format == "test":
            next_result = result_queue.receiver.get()
            while next_result != 'EOF':
                output = next_result
        else:
            output = []
            next_result = result_queue.receiver.get()
            while next_result != 'EOF':
                output += [next_result]
        return Output(output)
    else:
        return None
    
def restart_processes():
    done = stop_processes()
    time.sleep(0.5)
    start_processes()

def stop_processes():
    VALIDATION_RUNNER.stop_process()
    CONTACT_SOURCE_RUNNER.stop_process()
    XJOIN_RUNNER.stop_process()
    POST_PROCESSING_RUNNER.stop_process()
    time.sleep(0.1)

def start_processes():
    VALIDATION_RUNNER.start_process()
    CONTACT_SOURCE_RUNNER.start_process()
    XJOIN_RUNNER.start_process()
    POST_PROCESSING_RUNNER.start_process()
    time.sleep(0.1)
