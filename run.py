from flask import Flask, request, Response
from SPARQLWrapper import SPARQLWrapper
from rdflib import term

import rdflib
import sys
import os
import time
import logging


sys.path.append('./travshacl')
from travshacl.reduction.ReducedShapeNetwork import ReducedShapeNetwork
from travshacl.validation.core.GraphTraversal import GraphTraversal
sys.path.remove('./travshacl')

from app.query import Query
from app.utils import printSet, pathToString
from app.tripleStore import TripleStore
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

    # Extract Triples of the given Query to identify the mentioned Shape (?x --> s_id)
    query_triples = query.triples
    possible_shapes = set()
    for row in ShapeGraph.queryTriples(query_triples):
        possible_shapes.add(ShapeGraph.uriRefToShapeId(row[0]))
    
    assert(len(possible_shapes) == 1)
    s_id = list(possible_shapes)[0]

    print('The Query referres to {}'.format(s_id))

    if globals.shape_queried[s_id] == False:
        # Extract Pathes from the Target Shape to the identified Shape
        paths = Path.computePathsToTargetShape(s_id,[])
        print('Paths: ' + pathToString(paths))

        for path in paths:
            construct_query = Query.constructQueryFrom(globals.targetShape,globals.initial_query_triples,path,s_id)
            #print("Construct Query: ")
            #print(str(construct_query) + '\n')
            SubGraph.extendWithConstructQuery(construct_query)
        globals.shape_queried[s_id] = True

    # Query the internal subgraph with the given input query
    print("Query Subgraph:")
    start = time.time()
    result = SubGraph.query(query, s_id)
    json = result.serialize(encoding='utf-8',format='json')
    end = time.time()
    print("Execution took " + str((end - start)*1000) + ' ms')
    print('\033[92m-------------------------------------------------------------\033[00m')

    return Response(json, mimetype='application/json')

@app.route("/queryShapeGraph", methods = ['POST'])
def queryShapeGraph():
    query = Query(request.form['query'])
    result = ShapeGraph.query(query.parsed_query)
    for row in result:
        print(row)
    return "Done"
    
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
    SubGraph.clear()
    ShapeGraph.clear()
    globals.referred_by = dict()
    globals.shape_to_var = dict()
    globals.targetShape = None

    # Parse POST Arguments
    task = Eval.parse_task_string(request.form['task'])    
    traversal_strategie = Eval.parse_traversal_string(request.form['traversalStrategie'])
    schema_directory = request.form['schemaDir']
    heuristics = Eval.parse_heuristics_string(request.form['heuristic'])
    query_string = request.form['query']
    globals.targetShape = request.form['targetShape']

    # Parse Config File
    config = Configs.read_and_check_config('config.json')
    globals.endpoint = SPARQLWrapper(config['external_endpoint'])

    os.makedirs(os.getcwd() + '/' + schema_directory, exist_ok=True)
    
    initial_query = Query(query_string)

    # Step 1 and 2 are executed by ReducedShapeParser
    globals.network = ReducedShapeNetwork(schema_directory, config['shapeFormat'], INTERNAL_SPARQL_ENDPOINT, traversal_strategie, task,
                            heuristics, config['useSelectiveQueries'], config['maxSplit'],
                            config['outputDirectory'], config['ORDERBYinQueries'], config['SHACL2SPARQLorder'], initial_query, globals.targetShape, config['workInParallel'])

    # Setup of the ShapeGraph
    ShapeGraph.setPrefixes(initial_query.parsed_query.prologue.namespace_manager.namespaces())
    ShapeGraph.constructAndSetGraphFromShapes(globals.network.shapes)
    
    # Construct globals.referred_by Dictionary (used to build Paths to Target Shapes)
    for s in globals.network.shapes:
        for obj,pred in s.referencedShapes.items():
            if not obj in globals.referred_by:
                globals.referred_by[obj] = []
            globals.referred_by[obj].append({'shape': s.id, 'pred': pred})
    print('\nReferred by Dictionary: ' + str(globals.referred_by))

    # Set a Variable for each Shape
    VariableStore.setShapeVariables(globals.targetShape, globals.network.shapes)
    print('\nVariables to Shape Mapping: ' + str(globals.shape_to_var))

    print('\n-------------------Triples used for Construct Queries-------------------')
    # Build TripleStores for each Shape
    for s in globals.network.shapes:
        TripleStore.fromShape(s)
        print(s.id)
        printSet(TripleStore(s.id).getTriples())
    
    globals.initial_query_triples = initial_query.triples
    for query_triple in globals.initial_query_triples.copy():
        if not isinstance(query_triple.object, term.URIRef):
            globals.initial_query_triples.remove(query_triple)
    print('Initial Query Triples')
    printSet(globals.initial_query_triples)

    for s in globals.network.shapes:
        globals.shape_queried[s.id] = False
    
    # Extract query_triples of the input query to construct a query such that our Subgraph can be initalized
    SubGraph.extendWithConstructQuery(Query.constructQueryFrom(globals.targetShape,globals.initial_query_triples,[],globals.targetShape))
    globals.shape_queried[globals.targetShape] = True

    # Run the evaluation of the SHACL constraints over the specified endpoint
    report = globals.network.validate()  
    return report