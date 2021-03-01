from flask import Flask, request, Response
from SPARQLWrapper import SPARQLWrapper, JSON

import os, time, logging, json

import sys
sys.path.append('./travshacl') # Makes travshacl Package accesible without adding __init__.py to travshacl/ Directory
from reduction.ReducedShapeNetwork import ReducedShapeNetwork
import arg_eval_utils as Eval
import validation.sparql.SPARQLPrefixHandler as SPARQLPrefixHandler
sys.path.remove('./travshacl')
from app.query import Query
import app.colors as Colors


from app.outputCreation import QueryReport
import config_parser as Configs


app = Flask(__name__)
logging.getLogger('werkzeug').disabled = True

INTERNAL_SPARQL_ENDPOINT = "http://localhost:5000/endpoint"
ENDPOINT = None

@app.route("/endpoint", methods=['GET','POST'])
def endpoint():
    global ENDPOINT
    print(Colors.green('-------------------SPARQL Endpoint Request-------------------'))
    # Preprocessing of the Query
    if request.method == 'POST':
        query = request.form['query']
    if request.method == 'GET':
        query = request.args['query']

    print("Received Query: ")
    print(Colors.grey(query))

    start = time.time()
    ENDPOINT.setQuery(query)
    ENDPOINT.setReturnFormat(JSON)
    result = ENDPOINT.query().convert()
    jsonResult = json.dumps(result)
    end = time.time()
    
    print("Got {} result bindings".format(len(result['results']['bindings'])))
    print("Execution took " + str((end - start)*1000) + ' ms')
    print(Colors.green('-------------------------------------------------------------'))

    return Response(jsonResult, mimetype='application/json')
    
@app.route("/go", methods=['POST'])
def run():
    '''
    Go Route: Here we replace the main.py and Eval.py of travshacl.
    Arguments:
        POST:
            - task
            - traversalStrategie
            - schemaDir
            - heuristic
            - query
            - targetShape
    '''
    # Clear Globals
    global ENDPOINT
    ENDPOINT = None
    print(Colors.magenta('---------------------New Validation Task---------------------'))

    # Parse POST Arguments
    task = Eval.parse_task_string(request.form['task'])    
    traversal_strategie = Eval.parse_traversal_string(request.form['traversalStrategie'])
    schema_directory = request.form['schemaDir']
    heuristics = Eval.parse_heuristics_string(request.form['heuristic'])
    query_string = request.form['query']
    targetShapeID = request.form['targetShape']

    # Parse Config File
    if 'config' in request.form:
        config = Configs.read_and_check_config(request.form['config'])
        print("Using Custom Config: {}".format(request.form['config']))
    else:
        print("Using default config File!!")
        config = Configs.read_and_check_config('config.json')

    #DEBUG FLAG, set for test runs with additional output
    DEBUG_OUTPUT = config['advancedOutput']

    output_directory = config['outputDirectory']
    endpoint_url = config['external_endpoint']
    ENDPOINT = SPARQLWrapper(endpoint_url)

    if DEBUG_OUTPUT:
        endpoint_url = INTERNAL_SPARQL_ENDPOINT

    os.makedirs(os.path.join(os.getcwd(), output_directory), exist_ok=True)

    #Parse query_string into a corresponding select_query
    query = Query.prepare_query(query_string)

    SPARQLPrefixHandler.prefixes = {str(key):"<" + str(value) + ">" for (key,value) in query.namespace_manager.namespaces()}
    SPARQLPrefixHandler.prefixString = "\n".join(["".join("PREFIX " + key + ":" + value) for (key, value) in SPARQLPrefixHandler.prefixes.items()]) + "\n"

    # Step 1 and 2 are executed by ReducedShapeParser
    network = ReducedShapeNetwork(
        schema_directory, config['shapeFormat'], endpoint_url, traversal_strategie, task,
        heuristics, config['useSelectiveQueries'], config['maxSplit'], output_directory, 
        config['ORDERBYinQueries'], config['SHACL2SPARQLorder'], query, targetShapeID, 
        config['outputs'], config['workInParallel'], initial_query=query
    )

    # Run the evaluation of the SHACL constraints over the specified endpoint
    report = network.validate()

    # Retrieve the complete result for the initial query
    query_string = query.as_result_query()
    ENDPOINT.setQuery(query_string)
    ENDPOINT.setReturnFormat(JSON)
    results = ENDPOINT.query().convert()

    q = QueryReport(report, query, results)
    valid = q.full_report
    #valid = QueryReport.create_output(report, query, results)

    if DEBUG_OUTPUT:
        #New output generator, based on intersection of query and validation results
        reportResults = {}
        for shape, instance_dict in report.items():
            for is_valid, instances in instance_dict.items():
                for instance in instances:
                    reportResults[instance[1]] = (instance[0], is_valid, shape)

        queryResults = {}
        for binding in results['results']['bindings']:
            instance = binding[query.target_var[1:]]['value']
            queryResults[instance] = {var: info['value'] for var, info in binding.items()}
        
        #valid dict is left only for test purposes, no need to change the test cases
        valid = {"validTargets":[], "invalidTargets":[], "advancedValid":[], "advancedInvalid":[]}
        for t in reportResults.keys() & queryResults.keys():
            #'validation' : (instance shape, is_valid, violating/validating shape)
            if reportResults[t][0] == targetShapeID:
                if reportResults[t][1] == 'valid_instances':
                    valid["validTargets"].append((t, reportResults[t][2]))
                elif reportResults[t][1] == 'invalid_instances':
                    valid["invalidTargets"].append((t, reportResults[t][2]))
        for t in reportResults:
            #'validation' : (instance's shape, is_valid, violating/validating shape)
            if reportResults[t][0] != targetShapeID:
                if reportResults[t][1] == 'valid_instances':
                    valid["advancedValid"].append((t, reportResults[t][2]))
                elif reportResults[t][1] == 'invalid_instances':
                    valid["advancedInvalid"].append((t, reportResults[t][2]))
    print(Colors.magenta('-------------------------------------------------------------'))

    return Response(json.dumps(valid), mimetype='application/json')

@app.route("/", methods=['GET'])
def hello_world():
    return "Hello World"

if __name__ == '__main__':
    app.run(debug=True)