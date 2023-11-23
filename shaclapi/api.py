"""This module offers the main functionalities of the shaclAPI to the user.

The shaclAPI uses Python's multiprocessing capabilities for parallel execution of the SHACL validation during SPARQL query execution.
Due to delays occurring when parsing SPARQL queries with rdflib for the first time in each process, importing this module or parts of it will start a process for each task-type the shaclAPI needs to execute. These processes will stay running and wait for tasks to process.
"""


import json
import logging
import os
import re

from shaclapi.config import Config
from shaclapi.multiprocessing.contactSource import contactSource
from shaclapi.multiprocessing.functions import mp_validate, mp_xjoin, mp_post_processing, mp_output_completion
from shaclapi.multiprocessing.runner import Runner
from shaclapi.output import Output
from shaclapi.query import Query
from shaclapi.reduction import prepare_validation
from shaclapi.reduction.ValidationResultTransmitter import ValidationResultTransmitter
from shaclapi.statsCalculation import StatsCalculation

logger = logging.getLogger(__name__)

# This seems to load some pyparsing stuff and will speed up the execution of the first task by 1 second.
query = Query.prepare_query('PREFIX test1:<http://example.org/testGraph1#>\nSELECT DISTINCT ?x WHERE {\n?x a test1:classE.\n?x test1:has ?lit.\n}')
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

# Queues to collect statistics: --> {'topic':...., '':....}
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
    """Convenience function to get a multiprocessing queue object, which can be used as a result_queue in :func:`shaclapi.api.run_multiprocessing`.
    
    Returns
    -------
    python.multiprocessing.Queue
        A queue usable in :func:`shaclapi.api.run_multiprocessing`.
    """
    return OUTPUT_COMPLETION_RUNNER.get_new_out_queues(use_pipes=False)[0]


def run_multiprocessing(pre_config, result_queue=None):
    """Main function of the shaclAPI: Given a dictionary of configuration keys (properties in :py:mod:`shaclapi.config`) with the configured values, the shaclAPI starts the parallel execution of the SHACL validation during SPARQL query execution, while applying the activated heuristics.

    The following directed graph demonstrates the principal procedure. (Nodes represent tasks/processes and edges represent queues for colaboration):
    
    .. image:: procedure.png
       :align: center

    """
    # Parse Config from POST Request and Config File
    config = Config.from_request_form(pre_config)
    logger.info("To reproduce this call to the API run: run_config.py -c '" + json.dumps(config.config_dict) + "'")
    os.makedirs(os.path.abspath(config.output_directory), exist_ok=True)
    if config.save_outputs:
        os.makedirs(os.path.join(config.output_directory, config.backend, re.sub(r'[^\w\-_.]', '_', config.test_identifier)), exist_ok=True)

    # Check if query is given
    if config.query is None:
        raise Exception('The query to be executed over the SPARQL endpoint needs to be provided to the shaclAPI using the option query.')

    # Setup Stats Calculation
    statsCalc = StatsCalculation(test_identifier=config.test_identifier, approach_name=os.path.basename(config.config) if '{' not in config.config else 'dict_passed_to_shaclAPI')
    statsCalc.globalCalculationStart()

    # Set up the multiprocessing queue, which will give the final output.
    if result_queue is not None:
        QUEUE_OUTPUT = True
    else:
        result_queue = OUTPUT_COMPLETION_RUNNER.get_new_out_queues(config.use_pipes)[0]
        QUEUE_OUTPUT = False

    # Preparing the multiprocessing queues
    # 1. Create new queues for the given request
    stats_out_queue = CONTACT_SOURCE_RUNNER.get_new_queue()
    contact_source_out_queues = CONTACT_SOURCE_RUNNER.get_new_out_queues(config.use_pipes)
    validation_out_queues = VALIDATION_RUNNER.get_new_out_queues(config.use_pipes)
    xjoin_out_queues = XJOIN_RUNNER.get_new_out_queues(config.use_pipes)
    post_processing_out_queues = POST_PROCESSING_RUNNER.get_new_out_queues(config.use_pipes)
    output_completion_out_queues = (result_queue, )

    # 2. Extract Out Queues
    transformed_query_queue = contact_source_out_queues[0]  # pylint: disable=unbalanced-tuple-unpacking
    val_queue = validation_out_queues[0]  # pylint: disable=unbalanced-tuple-unpacking
    joined_results_queue = xjoin_out_queues[0]
    final_result_queue, timestamp_queue = post_processing_out_queues  # pylint: disable=unbalanced-tuple-unpacking

    # 3. Collect the sender parts of the queues.
    contact_source_out_connections = tuple((queue_adapter.sender for queue_adapter in contact_source_out_queues))
    validation_out_connections = tuple((queue_adapter.sender for queue_adapter in validation_out_queues))
    xjoin_out_connections = tuple((queue_adapter.sender for queue_adapter in xjoin_out_queues))
    post_processing_out_connections = tuple((queue_adapter.sender for queue_adapter in post_processing_out_queues))
    output_completion_out_connections = tuple((queue_adapter.sender for queue_adapter in output_completion_out_queues))

    # 4. Collect the receiver parts of the queues.
    contact_source_in_connections = tuple()
    validation_in_connections = tuple()
    xjoin_in_connections = (transformed_query_queue.receiver, val_queue.receiver)
    post_processing_in_connections = (joined_results_queue.receiver, )
    output_completion_in_connections = (final_result_queue.receiver, )

    # Setup of the validation result transmitting strategy (SHACL engine --> API).
    # This allows to process SHACL validation results as soon as they arrive.
    result_transmitter = ValidationResultTransmitter(output_queue=val_queue.sender, first_val_time_queue=stats_out_queue)

    # Parse query_string into a corresponding Query Object
    query = Query.prepare_query(config.query)
    query_starshaped = query.make_starshaped()

    collect_all_validation_results = config.collect_all_validation_results

    # Sanitizing the input  
    if query_starshaped is None:
        if not collect_all_validation_results and not isinstance(config.target_shape, dict):
            collect_all_validation_results = True
            logger.warning('Running in blocking mode as the target variable(s) could not be identified!')
        if config.replace_target_query and not isinstance(config.target_shape, dict):
            config.replace_target_query = False
            logger.warning('Can only replace target query if query is star-shaped!')
    else:
        query = query_starshaped

    if config.target_shape is None:
        if not collect_all_validation_results:
            collect_all_validation_results = True
            logger.warning('Running in blocking mode as the target shape is not given!')
        if config.replace_target_query:
            config.replace_target_query = False
            logger.warning('Can only replace target query if target shape is given!')
        if config.prune_shape_network:
            config.prune_shape_network = False
            logger.warning('Can only prune shape schema if target shape is given!')
        if config.start_with_target_shape:
            config.start_with_target_shape = False
            logger.warning('Can only start with target shape if target shape is given!')

    if not isinstance(config.target_shape, dict):  # Unify target shape -> {?var: list of shapes}
        config.target_shape = unify_target_shape(config.target_shape, query_starshaped)

    # The information we need depends on the output format:
    if config.output_format == 'test' or (not config.reasoning):
        query_to_be_executed = query.copy()
    else:
        query_to_be_executed = query.as_result_query()

    statsCalc.taskCalculationStart()

    # Start Processing Pipeline e.g. assigning each process a new task.
    # 1. Get the Data
    contact_source_task_description = (config.external_endpoint, query_to_be_executed.query_string, -1)
    CONTACT_SOURCE_RUNNER.new_task(contact_source_in_connections, contact_source_out_connections, contact_source_task_description, stats_out_queue, config.run_in_serial)

    validation_task_description = (config, query_to_be_executed.copy(), result_transmitter)
    VALIDATION_RUNNER.new_task(validation_in_connections, validation_out_connections, validation_task_description, stats_out_queue, config.run_in_serial)

    # 2. Join the Data
    xjoin_task_description = (config,)
    XJOIN_RUNNER.new_task(xjoin_in_connections, xjoin_out_connections, xjoin_task_description, stats_out_queue, config.run_in_serial)

    # 3. Post-Processing: Restore missing vars (these one which could not find a join partner (literals etc.))
    post_processing_task_description = (query_to_be_executed.PV, config.target_shape, query_to_be_executed.target_var, collect_all_validation_results)
    POST_PROCESSING_RUNNER.new_task(post_processing_in_connections, post_processing_out_connections, post_processing_task_description, stats_out_queue, config.run_in_serial)

    # 4. Transform to Outputformat
    output_completion_task_description = (query.copy(), config.target_shape, config.output_format == 'test')
    OUTPUT_COMPLETION_RUNNER.new_task(output_completion_in_connections, output_completion_out_connections, output_completion_task_description, stats_out_queue, config.run_in_serial)

    if config.write_stats:
        # matrix_file = os.path.join(os.path.abspath(config.output_directory), 'matrix.csv')
        # trace_file = os.path.join(os.path.abspath(config.output_directory), 'trace.csv')
        stats_file = os.path.join(os.path.abspath(config.output_directory), 'stats.csv')
    else:
        # matrix_file = None
        # trace_file = None
        stats_file = None

    try:
        # statsCalc.receive_and_write_trace(trace_file, timestamp_queue.receiver)
        statsCalc.receive_global_stats(stats_out_queue, using_output_completion_runner=True)
        statsCalc.write_matrix_and_stats_files(None, stats_file)
    except Exception as e:
        import sys
        import traceback
        exc_type, exc_value, exc_traceback = sys.exc_info()
        emsg = repr(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logger.exception(str(emsg))
        result_queue.sender.put('EOF')
        return emsg

    if not QUEUE_OUTPUT:
        next_result = result_queue.receiver.get()
        output = []
        if config.output_format == 'test':
            while next_result != 'EOF':
                output = next_result
                next_result = result_queue.receiver.get()
                logger.info(len(output['validTargets']), len(output['invalidTargets']))
        else:
            while next_result != 'EOF':
                output += [next_result]
                next_result = result_queue.receiver.get()
        logger.debug('Finished collecting results!')
        return Output(output)
    else:
        return None


def _make_list(x):
    """Creates a list from the object passed."""
    return x if isinstance(x, list) else [x]


def unify_target_shape(target_shape, query):
    """Given a target shape configuration (see :py:attr:`shaclapi.config.target_shape`) and a SPARQL query :class:`shaclapi.query.Query` a reformatted version of the target shape configuration is returned. The format is {?var: list of target shapes}, where ?var is a variable occuring in the query.
    
    Parameters
    ----------
    target_shape : dict, list or string
        A target shape configuration (see :py:attr:`shaclapi.config.target_shape`)

    query : shaclapi.query.Query
        The SPARQL query.
    """
    if isinstance(target_shape, dict):
        target_shape = {var.lower(): _make_list(shape) for var, shape in target_shape.items()}
    elif query is not None:
        target_shape = {query.target_var: _make_list(target_shape)}
    else:
        target_shape = {'UNDEF': _make_list(target_shape)}
    logger.debug(f'Unified target shape: {target_shape}')
    return target_shape


def only_reduce_shape_schema(pre_config):
    """Only reduces the given SHACL shape schema based on the provided target shape.

    The given SHACL shape schema is reduced to all shapes that are reachable from
    the provided target shape, i.e., they need to be validated in order to form
    a decision on the satisfaction of the instances of the target shape.

    Returns
    -------
    list
        A list with the names of the shapes in the reduced shape schema.
    """
    from shaclapi.reduction.travshacl.ReducedShapeParser import ReducedShapeParser
    from TravSHACL.core.GraphTraversal import GraphTraversal
    config = Config.from_request_form(pre_config)
    shape_parser = ReducedShapeParser(None, GraphTraversal.DFS, config)
    _, node_order, _ = shape_parser.parse_shapes(
        config.schema_directory, config.schema_format, True, 256, False)
    return node_order


def overlap_reduced_schemas(pre_config, shape_one, shape_two):
    """Computes the percentage of overlap for two reduced shape schemas.

    First, for both sets of shapes, the reduced shape schema is generated.
    Afterwards, the intersection of both shape schemas is computed.
    The percentage of overlap is the number of shapes in the intersection
    divided by the number of shapes in the smaller of the input shape schemas.

    Returns
    -------
    float
        The percentage of overlap in both reduced shape schemas based on
        the minimal number of shapes in the input shape schemas.
    """
    config_one = pre_config
    if not isinstance(shape_one, list):
        shape_one = [shape_one]
    reduced_schema_one = set()
    for shape in shape_one:
        config_one['target_shape'] = shape
        [reduced_schema_one.add(node) for node in only_reduce_shape_schema(config_one)]

    config_two = pre_config
    if not isinstance(shape_two, list):
        shape_two = [shape_two]
    reduced_schema_two = set()
    for shape in shape_two:
        config_two['target_shape'] = shape
        [reduced_schema_two.add(node) for node in only_reduce_shape_schema(config_two)]

    # max_size = max(len(reduced_schema_one), len(reduced_schema_two))
    min_size = min(len(reduced_schema_one), len(reduced_schema_two))
    intersection = set(reduced_schema_one).intersection(set(reduced_schema_two))
    inter_size = len(intersection)

    return float(inter_size / min_size) if min_size > 0 else 0


def validation_and_statistics(pre_config):
    """Validates a SHACL shape schema and provides additional statistics.

    The SHACL shape schema is validated based on the provided configuration.
    That includes the path of the SHACL shape schema as well as the heuristics
    used to optimize the validation performance.

    Returns
    -------
        JSON structure:
        {shape1:
            {valid: #valid instances,
            invalid: #invalid instances,
            columns: [column name 1, column name 2, ...],
            results: [[instance 1 data 1,instance 1 data 2, ...], [instance 2 data 1,instance 2 data 2, ...], ...]
            }
        shape2: {...}
        ...
        }
    -------
    dict
       The result includes per-shape counts of the valid and invalid instances as
       well as a Boolean per instance of the shape stating its satisfaction of the
       shape's constraints.
    """
    from multiprocessing import Queue
    config = Config.from_request_form(pre_config)
    queue = Queue()
    result_transmitter = ValidationResultTransmitter(output_queue=queue)

    query = config.query
    if query is not None:
        query = Query.prepare_query(config.query)
        query_starshaped = query.make_starshaped()
        config.target_shape = unify_target_shape(config.target_shape, query_starshaped)

    shape_schema = prepare_validation(config, Query(config.query) if query is not None else None, result_transmitter)
    shape_schema.validate(config.start_with_target_shape)
    queue.put('EOF')

    val_results = {}
    item = queue.get()
    while item != 'EOF':
        instance = item['instance']
        val_shape = item['validation'][0]
        val_res = item['validation'][1]

        if val_shape not in val_results:
            val_results[val_shape] = {'valid': 0, 'invalid': 0, 'columns': [], 'results': []}
            val_results[val_shape]['columns'] = ['Data', 'Validation']
        val_results[val_shape]['valid' if val_res else 'invalid'] += 1
        val_results[val_shape]['results'].append([instance, 'Valid' if val_res else 'Invalid'])
        item = queue.get()
    queue.close()
    queue.cancel_join_thread()
    return val_results
