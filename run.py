from app.utils import prepare_validation
from flask import Flask, request, Response, g
import os, time, logging, json
from SPARQLWrapper import SPARQLWrapper, JSON
import multiprocessing as mp

from app.query import Query
import app.colors as Colors
from app.config import Config
from app.output.simpleOutput import SimpleOutput
from app.output.baseResult import BaseResult
from app.output.testOutput import TestOutput
from app.output.statsOutput import StatsOutput
from app.multiprocessing.functions import queue_output_to_table, mp_validate, mp_xjoin
from app.multiprocessing.runner import Runner
from app.multiprocessing.contactSource import contactSource
from app.reduction.ValidationResultTransmitter import ValidationResultTransmitter

app = Flask(__name__)
logging.getLogger('werkzeug').disabled = True

EXTERNAL_SPARQL_ENDPOINT: SPARQLWrapper = None
VALIDATION_RESULT_ENDPOINT = "http://localhost:5000/newValidationResult"

# Profiling Code
from pyinstrument import Profiler
global_request_count = 0

# This seems to load some pyparsing stuff and will speed up the execution of the first task by 1 second.
query = Query.prepare_query("PREFIX test1:<http://example.org/testGraph1#>\nSELECT DISTINCT ?x WHERE {\n?x a test1:classE.\n?x test1:has ?lit.\n}")
query.namespace_manager.namespaces()

# Building Multiprocessing Chain using Runners and Queries
VALIDATION_RUNNER = Runner(mp_validate)
val_queue, stats_out_queue_val = VALIDATION_RUNNER.get_out_queues()

CONTACT_SOURCE_RUNNER = Runner(contactSource, number_of_out_queues=2)
transformed_query_queue, query_queue, stats_out_queue_contact = CONTACT_SOURCE_RUNNER.get_out_queues()

XJOIN_RUNNER = Runner(mp_xjoin, in_queues=[transformed_query_queue, val_queue])
out_queue, stats_out_queue_xjoin  = XJOIN_RUNNER.get_out_queues()

# Starting the processes of the runners
VALIDATION_RUNNER.start_process()
CONTACT_SOURCE_RUNNER.start_process()
XJOIN_RUNNER.start_process()

@app.route("/endpoint", methods=['GET', 'POST'])
def endpoint():
    '''
    This is just an proxy endpoint to log the communication between the backend and the external sparql endpoint.
    '''
    global EXTERNAL_SPARQL_ENDPOINT
    print(Colors.green(Colors.headline('SPARQL Endpoint Request')))
    # Preprocessing of the Query
    if request.method == 'POST':
        query = request.form['query']
    if request.method == 'GET':
        query = request.args['query']

    print("Received Query: ")
    print(Colors.grey(query))

    start = time.time()
    EXTERNAL_SPARQL_ENDPOINT.setQuery(query)
    result = EXTERNAL_SPARQL_ENDPOINT.query().convert()
    jsonResult = json.dumps(result)
    end = time.time()

    print("Got {} result bindings".format(len(result['results']['bindings'])))
    print("Execution took " + str((end - start)*1000) + ' ms')
    print(Colors.green(Colors.headline('')))

    return Response(jsonResult, mimetype='application/json')

@app.route("/newValidationResult", methods=['POST'])
def enqueueValidationResult():
    global val_queue
    new_val_result = {'instance': request.form['instance'], 
                        'validation': (request.form['shape'], request.form['validation_result'] == 'valid', request.form['reason'])}
    print("Received", new_val_result)
    val_queue.put(new_val_result)
    return 'Ok'

@app.route("/multiprocessing", methods=['POST'])
def run_multiprocessing():
    '''
    Required Arguments:
        - query
        - targetShape
        - external_endpoint
        - schemaDir
    See app/config.py for a full list of available arguments!
    '''
    global_start_time = time.time()

    global EXTERNAL_SPARQL_ENDPOINT
    EXTERNAL_SPARQL_ENDPOINT = None

    # Parse Config from POST Request and Config File
    config = Config.from_request_form(request.form)

    # Setup of the Validation Result Transmitting Strategie
    if config.transmission_strategy == 'endpoint':
        result_transmitter = ValidationResultTransmitter(validation_result_endpoint=VALIDATION_RESULT_ENDPOINT, first_val_time_queue=stats_out_queue_xjoin, log_stats=log_stats)
    elif config.transmission_strategy == 'queue':
        result_transmitter = ValidationResultTransmitter(output_queue=val_queue, first_val_time_queue=stats_out_queue_xjoin, log_stats=config.output_format == "stats")
    else:
        result_transmitter = ValidationResultTransmitter(first_val_time_queue=stats_out_queue_xjoin, log_stats=config.output_format == "stats")

    EXTERNAL_SPARQL_ENDPOINT = SPARQLWrapper(config.external_endpoint, returnFormat=JSON)
    os.makedirs(os.path.join(os.getcwd(), config.output_directory), exist_ok=True)

    # Parse query_string into a corresponding Query Object    
    query = Query.prepare_query(config.query)

    # The information we need depends on the output format:
    if config.output_format == "test":
        query_to_be_executed = query.as_valid_query()
    else:
        query_to_be_executed = query.as_result_query()

    task_start_time = time.time()
    # 1.) Get the Data
    CONTACT_SOURCE_RUNNER.new_task(config.output_format == "stats", config.internal_endpoint if not config.send_initial_query_over_internal_endpoint else config.INTERNAL_SPARQL_ENDPOINT, query_to_be_executed, -1)
    VALIDATION_RUNNER.new_task(config.output_format == "stats", config, query, result_transmitter)

    # 2.) Join the Data
    XJOIN_RUNNER.new_task(config.output_format == "stats", config)

    # 3.) Result Collection: Order the Data and Restore missing vars (these one which could not find a join partner (literals etc.))
    if config.output_format == "stats":
        api_result = queue_output_to_table(out_queue, query_queue, stats_out_queue_xjoin)
    else:
        api_result = queue_output_to_table(out_queue, query_queue)


    # 4.) Output
    if config.output_format == "test":
        api_output = TestOutput.fromJoinedResults(config.target_shape,api_result)
    elif config.output_format == "simple":
        api_output = SimpleOutput.fromJoinedResults(api_result, query)
    elif config.output_format == "stats":
        TestOutput.fromJoinedResults(config.target_shape, api_result)
        approach_name = os.path.basename(config.config)
        api_output, matrix, traces = StatsOutput.from_queues(config.test_identifier,approach_name, global_start_time, task_start_time, stats_out_queue_contact, stats_out_queue_val, stats_out_queue_xjoin)
        output_directory = os.path.join(os.getcwd(), config.output_directory)
        matrix_file = os.path.join(output_directory, "matrix_" + approach_name + "_" + config.test_identifier + ".json")
        trace_file = os.path.join(output_directory, "trace_" + approach_name + "_" + config.test_identifier + ".json")
        stats_file = os.path.join(output_directory, "stats_" + approach_name + "_" + config.test_identifier + ".json")
        with open(matrix_file, "w") as f:
            json.dump(matrix,f, indent=4)
        with open(trace_file, "w") as f:
            f.write("test_name" + ',' + "approach" + ',' + "time" + ',' + "validation" + '\n')
            for trace in traces:
                f.write(trace["test_name"] + ',' + trace["approach"] + ',' + str(trace["time"]) + ',' + trace["validation"] + '\n')
            #json.dump(traces, f, indent=4)
        with open(stats_file, "w") as f:
            json.dump(api_output.output, f, indent=4)
    return Response(api_output.to_json(config.target_shape), mimetype='application/json')


@app.route("/singleprocessing", methods=['POST'])
def run():
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
    config = Config.from_request_form(request.form)
    
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
        return Response(TestOutput(BaseResult.from_travshacl(report, query, results)).to_json(config.target_shape), mimetype='application/json')
    else:
        return Response(str(SimpleOutput(BaseResult.from_travshacl(report, query, results))))

@app.route("/", methods=['GET'])
def hello_world():
    return "Hello World"

def start_profiling():
    g.profiler = Profiler()
    g.profiler.start()
    print(Colors.magenta(Colors.headline('New Validation Task')))

def stop_profiling():
    global global_request_count
    g.profiler.stop()
    output_html = g.profiler.output_html()
    global_request_count = global_request_count + 1
    with open("timing/api_profil{}.html".format(global_request_count - 1),"w") as f:
        f.write(output_html)
