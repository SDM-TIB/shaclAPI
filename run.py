from app.utils import parse_validation_params, prepare_validation
from flask import Flask, request, Response
import os, time, logging, json
from SPARQLWrapper import SPARQLWrapper, JSON
import multiprocessing as mp
from app.multiprocessing.contactSource import contactSource
from app.multiprocessing.Xjoin import XJoin
from copy import copy

from app.query import Query
import app.colors as Colors
from app.output.simpleOutput import SimpleOutput
from app.output.baseResult import BaseResult
from app.output.testOutput import TestOutput

app = Flask(__name__)
logging.getLogger('werkzeug').disabled = True

EXTERNAL_SPARQL_ENDPOINT: SPARQLWrapper = None

# Profiling Code
# from pyinstrument import Profiler
# global_request_count = 0


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
    #TODO: receive validation instances and put the in a global multiprocessing queue
    pass


def mp_query(q, endpoint_url, query_string):
    endpoint = SPARQLWrapper(endpoint_url, returnFormat=JSON)
    endpoint.setQuery(query_string)
    q.put(endpoint.query().convert())

def mp_validate(q, query, *params):
    schema = prepare_validation(query, *params)
    report = schema.validate()
    for shape, instance_dict in report.items():
        for is_valid, instances in instance_dict.items():
            for instance in instances:
                q.put((instance[1], instance[0], (is_valid == 'valid_instances'), shape))
    q.put('EOF')
    
@app.route("/baseline", methods=['POST'])
def baseline():
    global EXTERNAL_SPARQL_ENDPOINT
    EXTERNAL_SPARQL_ENDPOINT = None

    # Parse POST Arguments
    query_string = request.form["query"]
    targetShapeID = request.form['targetShape']

    # Parse Config File
    params = parse_validation_params(request.form)
    config = params[-2]

    EXTERNAL_SPARQL_ENDPOINT = SPARQLWrapper(config["external_endpoint"], returnFormat=JSON)
    os.makedirs(os.path.join(os.getcwd(), config["outputDirectory"]), exist_ok=True)

    # Parse query_string into a corresponding select_query    
    query = Query.prepare_query(query_string)
    query_ctx = mp.get_context("spawn")
    val_ctx   = mp.get_context("spawn")
    
    query_queue = query_ctx.Queue()
    val_queue   = val_ctx.Queue()
    
    query_p = query_ctx.Process(target=contactSource, args=(config["external_endpoint"], query_string, query_queue, -1))
    val_p   = val_ctx.Process(target=mp_validate, args=(val_queue, query, *params))
    query_p.start()
    val_p.start()

    query_p.join()
    val_p.join()

    
    baseResult = BaseResult.from_travshaclBase(val_queue,query,query_queue)
    #print(SimpleOutput(copy(baseResult)))
    #print(baseResult.validation_report_triples)
    #print(baseResult.query_results)
    
    return Response(TestOutput(copy(baseResult)).to_json(targetShapeID), mimetype='application/json')


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
    print(Colors.magenta(Colors.headline('New Validation Task')))
    # Profiling Code
    # g.profiler = Profiler()
    # g.profiler.start()

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
    schema = prepare_validation(query, *params)
    
    # Run the evaluation of the SHACL constraints over the specified endpoint
    report = schema.validate()
    
    # Retrieve the complete result for the initial query
    query_string = query.as_result_query()

    EXTERNAL_SPARQL_ENDPOINT.setQuery(query_string)
    results = EXTERNAL_SPARQL_ENDPOINT.query().convert()

    print(Colors.magenta(Colors.headline('')))

    # Profiling Code
    # global global_request_count
    # g.profiler.stop()
    # output_html = g.profiler.output_html()
    # global_request_count = global_request_count + 1
    # with open("timing/profil{}.html".format(global_request_count - 1),"w") as f:
    #     f.write(output_html)
    
    if DEBUG_OUTPUT:
        return Response(TestOutput(BaseResult.from_travshacl(report, query, results)).to_json(targetShapeID), mimetype='application/json')
    else:
        return Response(SimpleOutput(BaseResult.from_travshacl(report, query, results)).to_json())


@app.route("/", methods=['GET'])
def hello_world():
    return "Hello World"


if __name__ == '__main__':
    app.run(debug=True)
