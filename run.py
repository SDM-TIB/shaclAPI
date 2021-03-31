from app.utils import parse_validation_params, prepare_validation
from flask import Flask, request, Response
import os, time, logging, json
from SPARQLWrapper import SPARQLWrapper, JSON
import multiprocessing as mp

from app.query import Query
import app.colors as Colors
from app.outputCreation import QueryReport


app = Flask(__name__)
logging.getLogger('werkzeug').disabled = True

EXTERNAL_SPARQL_ENDPOINT: SPARQLWrapper = None

# Profiling Code
# from pyinstrument import Profiler
# global_request_count = 0


@app.route("/endpoint", methods=['GET', 'POST'])
def endpoint():
    global EXTERNAL_SPARQL_ENDPOINT
    print(Colors.green('-------------------SPARQL Endpoint Request-------------------'))
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
    print(Colors.green('-------------------------------------------------------------'))

    return Response(jsonResult, mimetype='application/json')

def mp_query(q, endpoint_url, query_string):
    endpoint = SPARQLWrapper(endpoint_url, returnFormat=JSON)
    endpoint.setQuery(query_string)
    q.put(endpoint.query().convert())

def mp_validate(q, query, *params):
    schema = prepare_validation(query, *params)
    q.put(schema.validate())
    
@app.route("/baseline", methods=['POST'])
def baseline():
    global EXTERNAL_SPARQL_ENDPOINT
    EXTERNAL_SPARQL_ENDPOINT = None

    # Parse POST Arguments
    query_string = request.form["query"]

    # Parse Config File
    params = parse_validation_params(request.form)[:-1]
    config = params[-1]
    EXTERNAL_SPARQL_ENDPOINT = SPARQLWrapper(config["internal_endpoint"], returnFormat=JSON)
    os.makedirs(os.path.join(os.getcwd(), config["outputDirectory"]), exist_ok=True)

    # Parse query_string into a corresponding select_query    
    query = Query.prepare_query(query_string)
    query_ctx = mp.get_context("spawn")
    val_ctx   = mp.get_context("spawn")
    
    query_q = query_ctx.Queue()
    val_q   = val_ctx.Queue()
    
    query_p = query_ctx.Process(target=mp_query, args=(query_q, config["external_endpoint"], query_string))
    val_p   = val_ctx.Process(target=mp_validate, args=(val_q, query, *params))
    query_p.start()
    val_p.start()

    query_p.join()
    val_p.join()
    
    report = val_q.get()
    results = query_q.get()

    q = QueryReport(report, query, results)
    valid = q.full_report

    return Response(q.to_json(), mimetype='application/json')


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
    print(Colors.magenta('---------------------New Validation Task---------------------'))
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
    EXTERNAL_SPARQL_ENDPOINT = SPARQLWrapper(config["internal_endpoint"], returnFormat=JSON)
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

    q = QueryReport(report, query, results)
    valid = q.full_report
    # print(valid)

    if DEBUG_OUTPUT:
        # New output generator, based on intersection of query and validation results
        reportResults = {}
        for shape, instance_dict in report.items():
            for is_valid, instances in instance_dict.items():
                for instance in instances:
                    reportResults[instance[1]] = (instance[0], is_valid, shape)

        queryResults = {}
        for binding in results['results']['bindings']:
            instance = binding[query.target_var[1:]]['value']
            queryResults[instance] = {var: info['value']
                                      for var, info in binding.items()}

        # valid dict is left only for test purposes, no need to change the test cases
        valid = {"validTargets": [], "invalidTargets": [],
                 "advancedValid": [], "advancedInvalid": []}
        for t in reportResults.keys() & queryResults.keys():
            # 'validation' : (instance shape, is_valid, violating/validating shape)
            if reportResults[t][0] == targetShapeID:
                if reportResults[t][1] == 'valid_instances':
                    valid["validTargets"].append((t, reportResults[t][2]))
                elif reportResults[t][1] == 'invalid_instances':
                    valid["invalidTargets"].append((t, reportResults[t][2]))
        for t in reportResults:
            # 'validation' : (instance's shape, is_valid, violating/validating shape)
            if reportResults[t][0] != targetShapeID:
                if reportResults[t][1] == 'valid_instances':
                    valid["advancedValid"].append((t, reportResults[t][2]))
                elif reportResults[t][1] == 'invalid_instances':
                    valid["advancedInvalid"].append((t, reportResults[t][2]))
    print(Colors.magenta('-------------------------------------------------------------'))

    # Profiling Code
    # global global_request_count
    # g.profiler.stop()
    # output_html = g.profiler.output_html()
    # global_request_count = global_request_count + 1
    # with open("timing/profil{}.html".format(global_request_count - 1),"w") as f:
    #     f.write(output_html)
    return Response(json.dumps(valid), mimetype='application/json')


@app.route("/", methods=['GET'])
def hello_world():
    return "Hello World"


if __name__ == '__main__':
    app.run(debug=True)
