from app.utils import parse_validation_params, prepare_validation
from flask import Flask, request, Response, g
import os, time, logging, json
from SPARQLWrapper import SPARQLWrapper, JSON
import multiprocessing as mp
from app.multiprocessing.contactSource import contactSource
from copy import copy

from app.query import Query
import app.colors as Colors
from app.output.simpleOutput import SimpleOutput
from app.output.baseResult import BaseResult
from app.output.testOutput import TestOutput
from app.multiprocessing.transformer import queue_output_to_table, mp_validate, mp_xjoin
from app.multiprocessing.runner import Runner

app = Flask(__name__)
logging.getLogger('werkzeug').disabled = True

EXTERNAL_SPARQL_ENDPOINT: SPARQLWrapper = None

# Profiling Code
from pyinstrument import Profiler
global_request_count = 0

# Building Multiprocessing Chain using Runners and Queries
VALIDATION_RUNNER = Runner(mp_validate)
val_queue = VALIDATION_RUNNER.get_out_queues()[0]
CONTACT_SOURCE_RUNNER = Runner(contactSource, number_of_out_queues=2)
transformed_query_queue, query_queue_copy = CONTACT_SOURCE_RUNNER.get_out_queues()
XJOIN_RUNNER = Runner(mp_xjoin, in_queues=[transformed_query_queue, val_queue])
out_queue  = XJOIN_RUNNER.get_out_queues()[0]

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
    #TODO: receive validation instances and put them in a global multiprocessing queue
    pass

@app.route("/baseline", methods=['POST'])
def baseline():
    # # Profiling Code
    # g.profiler = Profiler()
    # g.profiler.start()

    global EXTERNAL_SPARQL_ENDPOINT, VALIDATION_RUNNER, CONTACT_SOURCE_RUNNER,XJOIN_RUNNER, out_queue, query_queue_copy
    EXTERNAL_SPARQL_ENDPOINT = None

    # Parse POST Arguments
    query_string = request.form["query"]
    targetShapeID = request.form['targetShape']

    # Parse Config File
    params = parse_validation_params(request.form) # Removing TargetShapeID --> prepare_validation will return unreduced shape schema
    config = params[-2]

    EXTERNAL_SPARQL_ENDPOINT = SPARQLWrapper(config["external_endpoint"], returnFormat=JSON)
    os.makedirs(os.path.join(os.getcwd(), config["outputDirectory"]), exist_ok=True)

    # Parse query_string into a corresponding select_query    
    query = Query.prepare_query(query_string)

    # 1.) Get the Data
    CONTACT_SOURCE_RUNNER.new_task(config["external_endpoint"], query_string, -1)
    VALIDATION_RUNNER.new_task(query, True, True, True, *params)

    # 2.) Join the Data
    XJOIN_RUNNER.new_task()

    # 3.) Result Collection: Order the Data and Restore missing vars (these one which could not find a join partner (literals etc.))
    api_result = queue_output_to_table(out_queue, query_queue_copy)

    # 4.) Output
    testOutput = TestOutput.fromJoinedResults(targetShapeID,api_result)
    
    # # Profiling Code
    # g.profiler.stop()
    # global global_request_count
    # output_html = g.profiler.output_html()
    # global_request_count = global_request_count + 1
    # with open("timing/profil{}.html".format(global_request_count - 1),"w") as f:
    #     f.write(output_html)
    return Response(testOutput.to_json(targetShapeID), mimetype='application/json')


@app.route("/go", methods=['POST'])
def run():
    '''
    Go Route: Here we replace the main.py and Eval.py of travshacl.
    Arguments:
        POST:
            - traversalStrategie
            - schemaDir
            - heuristic
            - query
            - targetShape
        CONFIG File:
            - debugging
            - external_endpoint
            - outputDirectory
            - shapeFormat
            - useSelectiveQueries
            - maxSplit
            - ORDERBYinQueries
            - SHACL2SPARQLorder
            - outputs
            - workInParallel
    '''
    # # Profiling Code
    # g.profiler = Profiler()
    # g.profiler.start()
    # print(Colors.magenta(Colors.headline('New Validation Task')))

    # Each run can be over a different Endpoint, so the endpoint needs to be recreated
    global EXTERNAL_SPARQL_ENDPOINT
    EXTERNAL_SPARQL_ENDPOINT = None

    # Parse POST Arguments
    query_string = request.form['query']
    targetShapeID = request.form['targetShape']

    # Parse Config File
    params = parse_validation_params(request.form)
    config = params[-2]
    DEBUG_OUTPUT = config["debugging"]
    EXTERNAL_SPARQL_ENDPOINT = SPARQLWrapper(config["external_endpoint"], returnFormat=JSON)
    os.makedirs(os.path.join(os.getcwd(), config["outputDirectory"]), exist_ok=True)

    # Parse query_string into a corresponding select_query
    query = Query.prepare_query(query_string)
    schema = prepare_validation(query, True, True, *params) # True means replace TargetShape Query
    
    # Run the evaluation of the SHACL constraints over the specified endpoint
    report = schema.validate(start_with_target_shape=True)
    
    # Retrieve the complete result for the initial query
    query_string = query.as_result_query()

    EXTERNAL_SPARQL_ENDPOINT.setQuery(query_string)
    results = EXTERNAL_SPARQL_ENDPOINT.query().convert()

    print(Colors.magenta(Colors.headline('')))

    # # Profiling Code
    # global global_request_count
    # g.profiler.stop()
    # output_html = g.profiler.output_html()
    # global_request_count = global_request_count + 1
    # with open("timing/api_profil{}.html".format(global_request_count - 1),"w") as f:
    #     f.write(output_html)

    if DEBUG_OUTPUT:
        return Response(TestOutput(BaseResult.from_travshacl(report, query, results)).to_json(targetShapeID), mimetype='application/json')
    else:
        return Response(SimpleOutput(BaseResult.from_travshacl(report, query, results)).to_json())


@app.route("/", methods=['GET'])
def hello_world():
    return "Hello World"


if __name__ == '__main__':
    # This seems to load some pyparsing stuff and will speed up the execution of the first task by 1 second.
    query = Query.prepare_query("PREFIX test1:<http://example.org/testGraph1#>\nSELECT DISTINCT ?x WHERE {\n?x a test1:classE.\n?x test1:has ?lit.\n}")
    query.namespace_manager.namespaces()
    
    # Starting the processes of the runners
    VALIDATION_RUNNER.start_process()
    CONTACT_SOURCE_RUNNER.start_process()
    XJOIN_RUNNER.start_process()
    app.run(debug=True)
