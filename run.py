from flask import Flask, request, Response
from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import term

import rdflib
import sys
import os
import time
import logging
import json
import re

sys.path.append('./travshacl')
from travshacl.reduction.ReducedShapeNetwork import ReducedShapeNetwork
from travshacl.validation.core.GraphTraversal import GraphTraversal
sys.path.remove('./travshacl')

from app.query import Query
from app.utils import printSet, pathToString
from app.tripleStore import TripleStore
from app.outputCreation import QueryReport
import app.subGraph as SubGraph
import app.globals as globals
import app.shapeGraph as ShapeGraph
import app.path as Path
import app.variableStore as VariableStore
import arg_eval_utils as Eval
import config_parser as Configs

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.disabled = True

INTERNAL_SPARQL_ENDPOINT = "http://localhost:5000/endpoint"
@app.route("/endpoint", methods=['GET','POST'])
def endpoint():
    print('\033[92m-------------------SPARQL Endpoint Request-------------------\033[00m')
    # Preprocessing of the Query
    if request.method == 'POST':
        query = Query(request.form['query'])
    if request.method == 'GET':
        query = Query(request.args['query'])

    print("Received Query: ")
    print('\033[02m' + str(query) + '\033[0m\n')

    start = time.time()
    result = SubGraph.queryExternalEndpoint(query)
    jsonResult = json.dumps(result)
    end = time.time()
    
    print("Got {} result bindings".format(len(result['results']['bindings'])))
    print("Execution took " + str((end - start)*1000) + ' ms')
    print('\033[92m-------------------------------------------------------------\033[00m')

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
    globals.targetShapeID = None
    globals.endpoint = None
    globals.filter_clause = ''
    globals.ADVANCED_OUTPUT = False

    # Parse POST Arguments
    task = Eval.parse_task_string(request.form['task'])    
    traversal_strategie = Eval.parse_traversal_string(request.form['traversalStrategie'])
    schema_directory = request.form['schemaDir']
    heuristics = Eval.parse_heuristics_string(request.form['heuristic'])
    query_string = request.form['query']
    globals.targetShapeID = request.form['targetShape']

    # Parse Config File
    if 'config' in request.form:
        config = Configs.read_and_check_config(request.form['config'])
        print("Using Custom Config: {}".format(request.form['config']))
    else:
        print("Using default config File!!")
        config = Configs.read_and_check_config('config.json')
    print(config)

    #Advanced output FLAG, set for test runs with additional output
    globals.ADVANCED_OUTPUT = config['advancedOutput']

    globals.endpoint = SPARQLWrapper(config['external_endpoint'])

    os.makedirs(os.getcwd() + '/' + schema_directory, exist_ok=True) #TODO: Do we need that?
    
    # Rename Variables in Initial Query to avoid overlapping Variable Names
    initial_query = Query(query_string)
    for i,variable in enumerate(initial_query.vars):
        if variable not in initial_query.queriedVars:
            query_string = query_string.replace(variable.n3(),'?q_{}'.format(i))

    # Assumption target variable (center of star) is the first variable in first triple occuring in the initial query
    if not '?x' in query_string:
        targetVar = initial_query.triples()[0].subject
        query_string = query_string.replace(targetVar.n3(),'?x')

    initial_query = Query(query_string)
    
    # Extract all the triples in the given initial query
    globals.initial_query_triples = initial_query.triples()    
    print('Initial Query Triples')
    printSet(globals.initial_query_triples)
    
    # Extract all FILTER terms
    filter_terms = re.findall('FILTER\(.*\)',initial_query.query,re.DOTALL)
    for i,filter_term in enumerate(filter_terms,start=1):
        if i != len(filter_terms):
            globals.filter_clause = globals.filter_clause + filter_term + '.\n'
        else:
            globals.filter_clause = globals.filter_clause + filter_term

    print('Initial Query Filters')
    printSet(filter_terms)

    newTargetDef = Query.targetDefFromStarShapedQuery(globals.initial_query_triples, globals.filter_clause)
    print("New Target Definition: " + str(newTargetDef))

    # Step 1 and 2 are executed by ReducedShapeParser
    network = ReducedShapeNetwork(schema_directory, config['shapeFormat'], INTERNAL_SPARQL_ENDPOINT, traversal_strategie, task,
                            heuristics, config['useSelectiveQueries'], config['maxSplit'],
                            config['outputDirectory'], config['ORDERBYinQueries'], config['SHACL2SPARQLorder'], initial_query, globals.targetShapeID, config['outputs'], config['workInParallel'], targetDefQuery= newTargetDef.query)

    print("Finished Step 1 and 2!")

    # Run the evaluation of the SHACL constraints over the specified endpoint
    report = network.validate()
    print(report)

    # Retrieve the complete result for the initial query
    globals.endpoint.setQuery(initial_query.query)
    globals.endpoint.setReturnFormat(JSON)
    results = globals.endpoint.query().convert()

    final_output = QueryReport.create_output(report, initial_query, results)
    print(final_output.full_report)

    #New output generator, based on intersection of query and validation results
    reportResults = {}
    for shape, instance_dict in report.items():
        for is_valid, instances in instance_dict.items():
            for instance in instances:
                reportResults[instance[1]] = (instance[0], is_valid, shape)

    queryResults = {}
    for binding in results['results']['bindings']:
        instance = binding['x']['value']
        queryResults[instance] = {var: info['value'] for var, info in binding.items()}
    
    #valid dict is left only for test purposes, no need to change the test cases
    valid = {"validTargets":[], "invalidTargets":[]}
    for t in reportResults.keys() & queryResults.keys():
        #'validation' : (instance shape, is_valid, violating/validating shape)
        if reportResults[t][0] == globals.targetShapeID:
            if reportResults[t][1] == 'valid_instances':
                valid["validTargets"].append((t, reportResults[t][2]))
            elif reportResults[t][1] == 'invalid_instances':
                valid["invalidTargets"].append((t, reportResults[t][2]))

    #Return full report, if ADVANCED_OUTPUT is set
    if globals.ADVANCED_OUTPUT:
        valid["advancedValid"] = []
        valid["advancedInvalid"] = []
        for t in reportResults:
            #'validation' : (instance's shape, is_valid, violating/validating shape)
            if reportResults[t][0] != globals.targetShapeID:
                if reportResults[t][1] == 'valid_instances':
                    valid["advancedValid"].append((t, reportResults[t][2]))
                elif reportResults[t][1] == 'invalid_instances':
                    valid["advancedInvalid"].append((t, reportResults[t][2]))

    return Response(json.dumps(valid), mimetype='application/json')

@app.route("/", methods=['GET'])
def hello_world():
    return "Hello World"

@app.route("/queryShapeGraph", methods = ['POST'])
def queryShapeGraph():
    query = Query(request.form['query'])
    result = ShapeGraph.query(query.parsed_query)
    for row in result:
        print(row)
    return "Done"

if __name__ == '__main__':
    app.run(debug=True)