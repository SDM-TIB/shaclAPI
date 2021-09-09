import os, logging, time, sys, json, re
from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib.namespace import RDF
from rdflib.term import Variable

from app.connectivity import Connectivity
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
from app.output.CSVWriter import CSVWriter
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

# Dataprocessing Queues/Pipes --> 'EOF' is written by the runner class after function to execute finished

# Name                      | Sender - Threads          | Receiver - Threads        | Queue/Pipe    | Description
# ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
# val_queue                 | VALIDATION_RUNNER         | XJOIN_RUNNER              | Pipe          | Queue with validation results
# shape_variables_queue     | VALIDATION_RUNNER         | POST_PROCESSING_RUNNER    | Pipe          |
# transformed_query_queue   | CONTACT_SOURCE_RUNNER     | XJOIN_RUNNER              | Pipe          | Query results in a joinable format 
# query_results_queue       | CONTACT_SOURCE_RUNNER     | POST_PROCESSING_RUNNER    | Pipe          | All results in original binding format
# joined_results_queue      | XJOIN_RUNNER              | POST_PROCESSING_RUNNER    | Pipe          | Joined results (literals/non-shape uris missing, and still need to collect bindings with similar id)
# final_result_queue        | POST_PROCESSING_RUNNER    | Main Thread               | Pipe          |

# Queues to collect statistics: --> {"topic":...., "":....}
# stats_out_queue           | ALL_RUNNER                | Main Thread               | Queue         | one time statistics per run --> known number of statistics (also contains exception notifications in case a runner catches an exception)
# timestamp_queue           | POST_PROCESSING_RUNNER    | Main Thread               | Pipe          | variable number of result timestamps per run --> close with 'EOF' by queue_output_to_table

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
    contact_source_out_queues = CONTACT_SOURCE_RUNNER.get_new_out_queues(config.use_pipes) 
    validation_out_queues = VALIDATION_RUNNER.get_new_out_queues(config.use_pipes)
    xjoin_out_queues = XJOIN_RUNNER.get_new_out_queues(config.use_pipes)
    post_processing_out_queues = POST_PROCESSING_RUNNER.get_new_out_queues(config.use_pipes)

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
        # with open("output/simpleOutput", "w") as d:
        #     d.write(str(api_output))
        #     #json.dump(api_output.to_json(config.target_shape),d)
        logger.debug(api_output.to_json(config.target_shape))
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
    schema = prepare_validation(config, query, result_transmitter)
    
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

def compute_experiment_metrices(pre_config):
    config = Config.from_request_form(pre_config)
    endpoint = SPARQLWrapper(config.external_endpoint, returnFormat=JSON)
    os.makedirs(os.path.join(os.getcwd(), config.output_directory), exist_ok=True)

    # Parse query_string into a corresponding select_query
    query = Query.prepare_query(config.query)
    conn = Connectivity(query, endpoint)

    schema = prepare_validation(config, query, None)
    shapes = [shape for shape in schema.shapes if shape]

    approach_name = os.path.basename(config.config).rsplit('.json', 1)[0]
    
    # 1.) Connectivity (Subgraph induced by Shape Schema --> only the shapes/vertices are reduced)
    id_to_targetTypes = {s.id: conn.URI(s.targetDef) for s in shapes}

    # Calculating some number used for checksums
    number_of_relevant_triples = conn.query_endpoint("SELECT COUNT(*) WHERE {?s a ?t . ?s ?p ?o FILTER(?t in "+ str(tuple(id_to_targetTypes.values())).replace("'","").replace(",)",")") +" )}")
    number_of_relevant_triples_per_type = {s_id: conn.query_endpoint(conn.query_generator(subject_type=t, add_spo=True)) for s_id,t in id_to_targetTypes.items()}

    assert number_of_relevant_triples == sum(number_of_relevant_triples_per_type.values())

    checksum = number_of_relevant_triples

    # Inter Shape Connections
    checksum = number_of_relevant_triples
    inter_shape_connections = {}
    for s in shapes:
        inter_shape_connections[s.id] = {}
        inter_shape_connections[s.id]['union'] = set()
        for s2 in shapes:
            predicates_between_s_s2 = conn.get_predicates_between(id_to_targetTypes[s.id], id_to_targetTypes[s2.id])
            inter_shape_connections[s.id][s2.id] = predicates_between_s_s2
            inter_shape_connections[s.id]['union'] = inter_shape_connections[s.id]['union'].union(predicates_between_s_s2)

    for s in shapes:
        for s2 in shapes:
            preds = inter_shape_connections[s.id][s2.id]
            for pred in preds:
                result = conn.query_endpoint(conn.query_generator(subject_type=id_to_targetTypes[s.id], predicate=pred, object_type=id_to_targetTypes[s2.id]))
                conn.new_result(id_to_targetTypes[s.id], pred, id_to_targetTypes[s2.id],result)
                checksum -= result
    
    # Intra Shape Connections
    intra_shape_connections = {}
    for s in shapes:
        intra_shape_connections[s.id] = conn.get_all_predicates(id_to_targetTypes[s.id]).difference(inter_shape_connections[s.id]['union'])

    for s in shapes:
        for pred in intra_shape_connections[s.id]:
            result = conn.query_endpoint(conn.query_generator(subject_type=id_to_targetTypes[s.id], predicate=pred))
            conn.new_result(id_to_targetTypes[s.id], pred, " ", result)
            checksum -= result

    conn.write_to_file(os.path.join(config.output_directory, f"connectivity_{config.test_identifier}_{approach_name}_shape_schema.csv"))

    # 1.2.) Connectivity (Subgraph induced by Query --> only contains all the triples that are used to answer the query: only target shape (one vertice) and all edges mentioned in the query)

    # Counting the number of triples per triple in star-shaped query
    for triple in query.triples:
        result = conn.query_endpoint(conn.query_generator(subject_type=id_to_targetTypes[config.target_shape], extras=["?s " + triple.predicate.n3() + " " + triple.object.n3() + "."]))
        conn.new_result(id_to_targetTypes[config.target_shape], triple.predicate.n3(), triple.object.n3() if not isinstance(triple.object, Variable) else " ", result)

    conn.write_to_file(os.path.join(config.output_directory, f"connectivity_{config.test_identifier}_{approach_name}_query.csv"))

    if checksum != 0:
        raise Exception("Global Checksum is {} instead of 0").format(checksum)

    # 2.) Shape Schema Metrices
    print("Shape Schema Metrics")
    def constraint_statistics(constraints):
        number_of_constraints = len(constraints)

        max_constraints = list(filter(lambda c: type(c).__name__ == "MaxOnlyConstraint", constraints))
        max_values = [c.max for c in max_constraints] if len(max_constraints) > 0 else [-1]

        min_constraints = list(filter(lambda c: type(c).__name__ == "MinOnlyConstraint", constraints))
        min_values = [c.min for c in min_constraints] if len(min_constraints) > 0 else [-1]

        min_max_constraints = list(filter(lambda c: type(c).__name__ == "MinMaxConstraint", constraints))
        mm_min_values = [c.min for c in min_max_constraints] if len(min_max_constraints) > 0 else [-1]
        mm_max_values = [c.max for c in min_max_constraints] if len(min_max_constraints) > 0 else [-1]


        type_of_constraints = {"max": (len(max_constraints), max(max_values)), 
                                "min": (len(min_constraints), max(min_values)), 
                                "minmax": (len(min_max_constraints), max(mm_min_values), max(mm_max_values))}
        return number_of_constraints, type_of_constraints

    for shape in shapes:
        print(shape.id)
        inter_shape_constraints = [constraint for constraint in shape.constraints if constraint.shapeRef]
        intra_shape_constraints = [constraint for constraint in shape.constraints if constraint.shapeRef is None]

        print("Inter Shape Constraints: ", constraint_statistics(inter_shape_constraints))
        print("Intra Shape Constraints: ", constraint_statistics(intra_shape_constraints))

