import os, logging, time, sys
from SPARQLWrapper import SPARQLWrapper, JSON
import multiprocessing as mp
import threading

from app.query import Query
import app.colors as Colors
from app.config import Config
from app.utils import lookForException
from app.output.simpleOutput import SimpleOutput
from app.output.testOutput import TestOutput
from app.multiprocessing.functions import queue_output_to_table, mp_validate, mp_xjoin, logger_thread
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
# Validation --> \
#                 XJoin --> Output Generation
# Query      --> /

# Dataprocessing Queues --> 'EOF' is written by the runner class after function to execute finished
# val_queue: Queue with validation results
# transformed_query_queue: Query results in a joinable format
# query_queue: All results in original binding format
# out_queue: Joined results (literals/non-shape uris missing, and still need to collect bindings with similar id)
# 
# Queues to collect statistics: --> {"topic":...., "":....}
# stats_out_queue: one time statistics per run --> known number of statistics (also contains exception notifications in case a runner catches an exception)
# result_timing_out_queue: variable number of result timestamps per run --> close with 'EOF' by queue_output_to_table

VALIDATION_RUNNER = Runner(mp_validate, number_of_out_queues=1)
CONTACT_SOURCE_RUNNER = Runner(contactSource, number_of_out_queues=2)
XJOIN_RUNNER = Runner(mp_xjoin, number_of_out_queues=1)

# Starting the processes of the runners
VALIDATION_RUNNER.start_process()
CONTACT_SOURCE_RUNNER.start_process()
XJOIN_RUNNER.start_process()

def run_multiprocessing(pre_config):
    global EXTERNAL_SPARQL_ENDPOINT
    EXTERNAL_SPARQL_ENDPOINT = None

    # Parse Config from POST Request and Config File
    config = Config.from_request_form(pre_config)
    logging.basicConfig(filename=config.log_file, filemode='a', format="[%(asctime)s - %(levelname)s] %(name)s - %(processName)s: %(msg)s", level=logging.DEBUG)
    logger.debug("Config: " +  str(config.config_dict))

    EXTERNAL_SPARQL_ENDPOINT = SPARQLWrapper(config.external_endpoint, returnFormat=JSON)
    os.makedirs(os.path.join(os.getcwd(), config.output_directory), exist_ok=True)

    # Setup Stats Calculation
    statsCalc = StatsCalculation(test_identifier = config.test_identifier, approach_name = os.path.basename(config.config))
    statsCalc.globalCalculationStart()

    # Setup Multiprocessing Queues
    result_timing_out_queue = mp.Queue()
    stats_out_queue = CONTACT_SOURCE_RUNNER.get_new_queue()
    log_queue = CONTACT_SOURCE_RUNNER.get_new_queue()
    contact_source_out_queues = CONTACT_SOURCE_RUNNER.get_new_out_queues()
    transformed_query_queue, query_queue = contact_source_out_queues
    validation_out_queues = VALIDATION_RUNNER.get_new_out_queues()
    val_queue = validation_out_queues[0]
    xjoin_out_queues = XJOIN_RUNNER.get_new_out_queues()
    out_queue = xjoin_out_queues[0]


    # Setup of the Validation Result Transmitting Strategie
    if config.transmission_strategy == 'queue':
        result_transmitter = ValidationResultTransmitter(output_queue=val_queue, first_val_time_queue=stats_out_queue)
    else:
        result_transmitter = ValidationResultTransmitter(first_val_time_queue=stats_out_queue)

    # Parse query_string into a corresponding Query Object
    query = Query.prepare_query(config.query)

    # The information we need depends on the output format:
    if config.output_format == "test":
        query_to_be_executed = query.as_valid_query()
    else:
        query_to_be_executed = query.as_result_query()

    statsCalc.taskCalculationStart()

    # 1.) Get the Data
    contact_source_task_description = (config.internal_endpoint if not config.send_initial_query_over_internal_endpoint else config.INTERNAL_SPARQL_ENDPOINT, query_to_be_executed, -1)
    contact_source_in_queues = tuple()
    CONTACT_SOURCE_RUNNER.new_task(contact_source_in_queues, contact_source_out_queues, contact_source_task_description, stats_out_queue,log_queue)

    validation_task_description = (config, query, result_transmitter)
    validation_in_queues = tuple()
    VALIDATION_RUNNER.new_task(validation_in_queues, validation_out_queues, validation_task_description, stats_out_queue, log_queue)
    
    # 2.) Join the Data
    xjoin_task_description = (config,)
    xjoin_in_queues = (transformed_query_queue, val_queue)
    XJOIN_RUNNER.new_task(xjoin_in_queues, xjoin_out_queues, xjoin_task_description, stats_out_queue, log_queue)

    # Setup Logging Thread
    log_thread = threading.Thread(target=logger_thread, args=(log_queue,))
    log_thread.start()

    # 3.) Result Collection: Order the Data and Restore missing vars (these one which could not find a join partner (literals etc.))
    try:
        if config.output_format == "stats":
            api_result = queue_output_to_table(out_queue, query_queue, config.queue_timeout, result_timing_out_queue)
        else:
            api_result = queue_output_to_table(out_queue, query_queue, config.queue_timeout)
    except Exception as e:
        logger.exception(Colors.magenta(repr(e)))
        restart_processes()
        if str(repr(e)) == "Empty()":
            return "Timeout while transforming join output to result bindings (according to queue_timeout config)!", config
        else:
            return str(repr(e)), config
    finally:
        log_queue.put(None)
        log_thread.join()

    # 4.) Output
    if config.output_format == "test":
        lookForException(stats_out_queue)
        api_output = TestOutput.fromJoinedResults(config.target_shape, api_result)
    elif config.output_format == "simple":
        lookForException(stats_out_queue)
        api_output = SimpleOutput.fromJoinedResults(api_result, query)
    elif config.output_format == "stats":
        TestOutput.fromJoinedResults(config.target_shape, api_result)
        statsCalc.globalCalculationFinished()

        output_directory = os.path.join(os.getcwd(), config.output_directory)
        matrix_file = os.path.join(output_directory, "matrix.csv")
        trace_file = os.path.join(output_directory, "trace.csv")
        stats_file = os.path.join(output_directory, "stats.csv")

        try:
            statsCalc.receive_and_write_trace(trace_file, result_timing_out_queue, config.queue_timeout)
            statsCalc.receive_global_stats(stats_out_queue, config.queue_timeout)
        except Exception as e:
            logger.exception(Colors.magenta(repr(e)))
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
    logging.basicConfig(filename=config.log_file, filemode='a', format="[%(asctime)s - %(levelname)s] %(name)s - %(processName)s: %(msg)s", level=logging.DEBUG)

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
    time.sleep(0.1)
    return not (VALIDATION_RUNNER.process_is_alive() or CONTACT_SOURCE_RUNNER.process_is_alive() or XJOIN_RUNNER.process_is_alive())

def start_processes():
    VALIDATION_RUNNER.start_process()
    CONTACT_SOURCE_RUNNER.start_process()
    XJOIN_RUNNER.start_process()
    time.sleep(0.1)
    return VALIDATION_RUNNER.process_is_alive() and CONTACT_SOURCE_RUNNER.process_is_alive() and XJOIN_RUNNER.process_is_alive()
