import os, logging, time, sys, json
from SPARQLWrapper import SPARQLWrapper, JSON
import multiprocessing as mp

from app.query import Query
from app.config import Config
from app.utils import lookForException
from app.output.simpleOutput import SimpleOutput
from app.output.testOutput import TestOutput
from app.multiprocessing.functions import mp_validate, mp_xjoin, mp_post_processing
from app.multiprocessing.runner import Runner
from app.multiprocessing.contactSource import contactSource
from app.reduction.ValidationResultTransmitter import ValidationResultTransmitter
from app.output.statsCalculation import StatsCalculation
from app.utils import prepare_validation
from app.output.baseResult import BaseResult

logger = logging.getLogger(__name__)

EXTERNAL_SPARQL_ENDPOINT: SPARQLWrapper = None
VALIDATION_RESULT_ENDPOINT = "http://localhost:5000/newValidationResult"

# This seems to load some pyparsing stuff and will speed up the execution of the first task by 1 second.
query = Query.prepare_query("PREFIX test1:<http://example.org/testGraph1#>\nSELECT DISTINCT ?x WHERE {\n?x a test1:classE.\n?x test1:has ?lit.\n}")
query.namespace_manager.namespaces()

# Building Multiprocessing Chain using Runners and Queries
#   /––––––––––– shape vars ––\
# Validation ––> \             \
#                 XJoin ––> PostProcessing ––> Output Generation
# Query      ––> /

# Dataprocessing Queues --> 'EOF' is written by the runner class after function to execute finished

# Name                      | Sender - Threads          | Receiver - Threads        | Queue/Pipe    | Description
# ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
# val_queue                 | VALIDATION_RUNNER         | XJOIN_RUNNER              | Pipe (Todo)   | Queue with validation results
# shape_variables_queue     | VALIDATION_RUNNER         | POST_PROCESSING_RUNNER    | Pipe (Todo)   |
# transformed_query_queue   | CONTACT_SOURCE_RUNNER     | XJOIN_RUNNER              | Pipe (Todo)   | Query results in a joinable format 
# query_results_queue       | CONTACT_SOURCE_RUNNER     | POST_PROCESSING_RUNNER    | Pipe (Todo)   | All results in original binding format
# joined_results_queue      | XJOIN_RUNNER              | POST_PROCESSING_RUNNER    | Pipe (Todo)   | Joined results (literals/non-shape uris missing, and still need to collect bindings with similar id)
# final_result_queue        | POST_PROCESSING_RUNNER    | Main Thread               | Pipe (Todo)   |

# Queues to collect statistics: --> {"topic":...., "":....}
# stats_out_queue           | ALL_RUNNER                | Main Thread               | Queue         | one time statistics per run --> known number of statistics (also contains exception notifications in case a runner catches an exception)
# timestamp_queue           | POST_PROCESSING_RUNNER    | Main Thread               | Pipe (Todo)   | variable number of result timestamps per run --> close with 'EOF' by queue_output_to_table

VALIDATION_RUNNER = Runner(mp_validate, number_of_out_queues=2)
CONTACT_SOURCE_RUNNER = Runner(contactSource, number_of_out_queues=2)
XJOIN_RUNNER = Runner(mp_xjoin, number_of_out_queues=1)
POST_PROCESSING_RUNNER = Runner(mp_post_processing, number_of_out_queues=2)

# Starting the processes of the runners
VALIDATION_RUNNER.start_process()
CONTACT_SOURCE_RUNNER.start_process()
XJOIN_RUNNER.start_process()
POST_PROCESSING_RUNNER.start_process()

def run_multiprocessing(pre_config):
    global EXTERNAL_SPARQL_ENDPOINT
    EXTERNAL_SPARQL_ENDPOINT = None

    # Parse Config from POST Request and Config File
    config = Config.from_request_form(pre_config)
    logger.debug("Config: " +  str(config.config_dict))

    EXTERNAL_SPARQL_ENDPOINT = SPARQLWrapper(config.external_endpoint, returnFormat=JSON)
    os.makedirs(os.path.join(os.getcwd(), config.output_directory), exist_ok=True)

    # Setup Stats Calculation
    statsCalc = StatsCalculation(test_identifier = config.test_identifier, approach_name = os.path.basename(config.config))
    statsCalc.globalCalculationStart()

    # Setup Multiprocessing Queues
    # 1.) Get Queues
    stats_out_queue = CONTACT_SOURCE_RUNNER.get_new_queue()
    contact_source_out_queues = CONTACT_SOURCE_RUNNER.get_new_out_queues() 
    validation_out_queues = VALIDATION_RUNNER.get_new_out_queues()
    xjoin_out_queues = XJOIN_RUNNER.get_new_out_queues()
    post_processing_out_queues = POST_PROCESSING_RUNNER.get_new_out_queues()

    # 2.) Extract Out Queues
    transformed_query_queue, query_results_queue = contact_source_out_queues # pylint: disable=unbalanced-tuple-unpacking
    val_queue, shape_variables_queue = validation_out_queues # pylint: disable=unbalanced-tuple-unpacking
    joined_results_queue = xjoin_out_queues[0]
    final_result_queue, timestamp_queue = post_processing_out_queues # pylint: disable=unbalanced-tuple-unpacking

    # 3.) Zip Out Connections
    contact_source_out_connections = tuple((queue_adapter.sender for queue_adapter in contact_source_out_queues))
    validation_out_connections = tuple((queue_adapter.sender for queue_adapter in validation_out_queues))
    xjoin_out_connections = tuple((queue_adapter.sender for queue_adapter in xjoin_out_queues))
    post_processing_out_connections = tuple((queue_adapter.sender for queue_adapter in post_processing_out_queues))

    # 3.) Zip In Connections
    contact_source_in_connections = tuple()
    validation_in_connections = tuple()
    xjoin_in_connections = (transformed_query_queue.receiver, val_queue.receiver)
    post_processing_in_connections = (shape_variables_queue.receiver, joined_results_queue.receiver, query_results_queue.receiver)


    # Setup of the Validation Result Transmitting Strategie
    if config.transmission_strategy == 'queue':
        result_transmitter = ValidationResultTransmitter(output_queue=val_queue.sender, first_val_time_queue=stats_out_queue)
    else:
        result_transmitter = ValidationResultTransmitter(first_val_time_queue=stats_out_queue)

    # Parse query_string into a corresponding Query Object
    query = Query.prepare_query(config.query)

    # The information we need depends on the output format:
    if config.output_format == "test" or (not config.reasoning):
        query_to_be_executed = query.as_valid_query()
    else:
        query_to_be_executed = query.as_result_query()

    statsCalc.taskCalculationStart()

    # Start Processing Pipeline
    # 1.) Get the Data
    contact_source_task_description = (config.internal_endpoint if not config.send_initial_query_over_internal_endpoint else config.INTERNAL_SPARQL_ENDPOINT, query_to_be_executed, -1)
    CONTACT_SOURCE_RUNNER.new_task(contact_source_in_connections, contact_source_out_connections, contact_source_task_description, stats_out_queue, config.run_in_serial)

    validation_task_description = (config, Query(query_to_be_executed), result_transmitter)
    VALIDATION_RUNNER.new_task(validation_in_connections, validation_out_connections, validation_task_description, stats_out_queue, config.run_in_serial)
    
    # 2.) Join the Data
    xjoin_task_description = (config,)
    XJOIN_RUNNER.new_task(xjoin_in_connections, xjoin_out_connections, xjoin_task_description, stats_out_queue, config.run_in_serial)

    # 3.) Post-Processing: Restore missing vars (these one which could not find a join partner (literals etc.))
    post_processing_task_description = (config.queue_timeout,)
    POST_PROCESSING_RUNNER.new_task(post_processing_in_connections, post_processing_out_connections, post_processing_task_description, stats_out_queue, config.run_in_serial)

    # 4.) Output
    if config.output_format == "test":
        lookForException(stats_out_queue)
        api_output = TestOutput.fromJoinedResults(config.target_shape, final_result_queue.receiver)
    elif config.output_format == "simple":
        lookForException(stats_out_queue)
        api_output = SimpleOutput.fromJoinedResults(query, final_result_queue.receiver)
    elif config.output_format == "stats":
        api_output = SimpleOutput.fromJoinedResults(query, final_result_queue.receiver)
        #with open("output/simpleOutput", "w") as d:
        #    d.write(str(api_output))
        #    #json.dump(api_output.to_json(config.target_shape),d)
        statsCalc.globalCalculationFinished()

        output_directory = os.path.join(os.getcwd(), config.output_directory)
        matrix_file = os.path.join(output_directory, "matrix.csv")
        trace_file = os.path.join(output_directory, "trace.csv")
        stats_file = os.path.join(output_directory, "stats.csv")

        try:
            statsCalc.receive_and_write_trace(trace_file, timestamp_queue.receiver, config.queue_timeout)
            statsCalc.receive_global_stats(stats_out_queue, config.queue_timeout)
        except Exception as e:
            logger.exception(repr(e))
            restart_processes()
            if str(repr(e)) == "Empty()":
                return "Timeout while calculating Statistics for the output (according to queue_timeout config)!", config
            else:
                return str(repr(e)), config

        api_output = statsCalc.write_matrix_and_stats_files(matrix_file, stats_file)

    return api_output, config

def run_singleprocessing(pre_config):
    '''
    ONLY COMPATIBLE WITH TRAVSHACL BACKEND!

    Required Arguments:
        - query
        - targetShape
        - external_endpoint
        - schemaDir
    See app/config.py for a full list of available arguments!
    '''
    # start_profiling()
    # Each run can be over a different Endpoint, so the endpoint needs to be recreated
    global EXTERNAL_SPARQL_ENDPOINT
    EXTERNAL_SPARQL_ENDPOINT = None
    result_transmitter = ValidationResultTransmitter()

    # Parse Config from POST Request and Config File
    config = Config.from_request_form(pre_config)

    EXTERNAL_SPARQL_ENDPOINT = SPARQLWrapper(config.external_endpoint, returnFormat=JSON)
    os.makedirs(os.path.join(os.getcwd(), config.output_directory), exist_ok=True)

    # Parse query_string into a corresponding select_query
    query = Query.prepare_query(config.query)
    schema = prepare_validation(config, query, result_transmitter) # True means replace TargetShape Query
    
    # Run the evaluation of the SHACL constraints over the specified endpoint
    report = schema.validate(start_with_target_shape=True)
    
    # Retrieve the complete result for the initial query
    EXTERNAL_SPARQL_ENDPOINT.setQuery(query.as_result_query())
    results = EXTERNAL_SPARQL_ENDPOINT.query().convert()
    # stop_profiling()
    if config.output_format == "test":
        return TestOutput(BaseResult.from_travshacl(report, query, results)), config
    else:
        return SimpleOutput(BaseResult.from_travshacl(report, query, results)), config

def restart_processes():
    done = stop_processes()
    time.sleep(0.5)
    done = done and start_processes()
    time.sleep(1)
    return done

def stop_processes():
    VALIDATION_RUNNER.stop_process()
    CONTACT_SOURCE_RUNNER.stop_process()
    XJOIN_RUNNER.stop_process()
    POST_PROCESSING_RUNNER.stop_process()
    time.sleep(0.1)
    return not (VALIDATION_RUNNER.process_is_alive() or CONTACT_SOURCE_RUNNER.process_is_alive() or XJOIN_RUNNER.process_is_alive() and POST_PROCESSING_RUNNER.process_is_alive())

def start_processes():
    VALIDATION_RUNNER.start_process()
    CONTACT_SOURCE_RUNNER.start_process()
    XJOIN_RUNNER.start_process()
    POST_PROCESSING_RUNNER.start_process()
    time.sleep(0.1)
    return VALIDATION_RUNNER.process_is_alive() and CONTACT_SOURCE_RUNNER.process_is_alive() and XJOIN_RUNNER.process_is_alive() and POST_PROCESSING_RUNNER.process_is_alive()
