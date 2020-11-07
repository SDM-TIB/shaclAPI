from flask import Flask, request, Response
import rdflib
import sys
import os
import logging
from SPARQLWrapper import SPARQLWrapper

sys.path.append('./travshacl')
from travshacl.validation.ShapeNetwork import ShapeNetwork
from travshacl.validation.core.GraphTraversal import GraphTraversal
sys.path.remove('./travshacl')

import app.subGraph as SubGraph
from app.query import Query
from app.utils import printSet
from app.tripleStore import TripleStore
from app.triple import setOfTriplesFromList
import app.globals as globals
import app.shapeGraph as ShapeGraph

import arg_eval_utils as Eval
import config_parser as Configs

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.disabled = True

INTERNAL_SPARQL_ENDPOINT = "http://localhost:5000/endpoint"
@app.route("/endpoint", methods=['GET','POST'])
def endpoint():
    # Preprocessing of the Query
    if request.method == 'POST':
        # printArgs(request.form)
        query = Query(request.form['query'])
    if request.method == 'GET':
        # printArgs(request.args)
        query = Query(request.args['query'])

    print("Query: ")
    print(str(query) + '\n')

    # Extract Triples of the given Query to identify the mentioned Shape (?x --> s_id)
    query_triples = setOfTriplesFromList(query.extract_triples())
    possible_shapes = set()
    for row in ShapeGraph.queryTriples(query_triples):
        possible_shapes.add(ShapeGraph.uriRefToShapeId(row[0]))
    print('Possible Shapes:')
    print(possible_shapes)
    assert(len(possible_shapes) == 1)
    s_id = list(possible_shapes)[0]
    print('s_id: ' + s_id)


    # TODO: Not assume Target Shape = Seed Shape
    if len(globals.shape_to_var) == 0:
        globals.shape_to_var[s_id] = [rdflib.term.Variable('x')]

    # Wenn sich andere Shapes s_i auf die aktuelle Shape s_id bezieht...
    if s_id in globals.referred_by:
        for referrer in globals.referred_by[s_id]:
            print('Referred by ' + str(referrer))
            print('Content of Shape_to_Var: ' + str(globals.shape_to_var))
            # Wenn die s_i schon eine Variable für s_id zugeordnet haben ...
            if referrer['shape'] in globals.shape_to_var:
                # dann ersetze jedes Vorkommen von ?x durch die jeweils vorkommenden Variable
                subject_list = globals.shape_to_var[referrer['shape']]
                predicat = rdflib.term.URIRef(ShapeGraph.extend(referrer['pred']))
                matching_vars = []
                print("Triples seen: ")
                print(TripleStore('seen_triples'))
                for s in subject_list:           
                    matching_vars = matching_vars + TripleStore('seen_triples').getObjectsWith(s,predicat)
                print('Matching var : ' + str(matching_vars))
                globals.shape_to_var[s_id] = matching_vars
    # Ersetzen der Variable ?x durch die in shape_to_var bestimmte, hier kann sich der Pfad aufteilen, sodass s_id Tripel öfter auftachen
    new_triples = set()
    print('shape_to_var :' + str(globals.shape_to_var[s_id]))
    for triple in query_triples:
        for var in globals.shape_to_var[s_id]:
            result_triple = triple.replaceX(var)
            new_triples.add(result_triple)

    print('New Triples :')
    for triple in new_triples:
        print(triple)
        
    # Construction of a new construct Query to update the internal subgraph
    construct_query = TripleStore('seen_triples').construct_query(new_triples)
    
    print("Construct Query: ")
    print(str(construct_query) + '\n')

    if construct_query != None:
        SubGraph.extendWithConstructQuery(construct_query)

    TripleStore('seen_triples').add(new_triples)

    # Query the internal subgraph with the given input query
    result = SubGraph.query(query.parsed_query)
    print("Number of triples seen: " + str(len(TripleStore('seen_triples'))))
    print("Triples seen: ")
    print(TripleStore('seen_triples'))
    print("Converting to json")
    print(len(result))
    json = result.serialize(encoding='utf-8',format='json')
    # print(dir(query.algebra()))
    print("-----------------------------------------------------------------")
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
    TripleStore('seen_triples').clear()
    SubGraph.clear()
    ShapeGraph.clear()
    globals.referred_by = dict()
    globals.referrd_by = dict()
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

    # Step 1 and 2 are executed by ReducedShapeParser
    globals.network = ShapeNetwork(schema_directory, config['shapeFormat'], INTERNAL_SPARQL_ENDPOINT, traversal_strategie, task,
                            heuristics, config['useSelectiveQueries'], config['maxSplit'],
                            config['outputDirectory'], config['ORDERBYinQueries'], config['SHACL2SPARQLorder'], config['workInParallel'], query_string, globals.targetShape)

    query = Query(query_string)

    # Setup of the ShapeGraph
    ShapeGraph.setPrefixes(query.parsed_query.prologue.namespace_manager.namespaces())
    ShapeGraph.constructAndSetGraphFromShapes(globals.network.shapes)
    
    # Construct globals.referred_by Dictionary
    for s in globals.network.shapes:
        for obj,pred in s.referencedShapes.items():
            if not obj in globals.referred_by:
                globals.referred_by[obj] = []
            globals.referred_by[obj].append({'shape': s.id, 'pred': pred})
    print('Referred by Dictionary: ' + str(globals.referred_by))

    # Extract query_triples of the input query to construct a query such that the our Subgraph can be initalized
    query_triples = setOfTriplesFromList(query.extract_triples())
    construct_query = TripleStore('seen_triples').construct_query(query_triples)
    SubGraph.extendWithConstructQuery(construct_query)

    # And store queried triples
    TripleStore('seen_triples').add(query_triples)

    # Run the evaluation of the SHACL constraints over the specified endpoint
    report = globals.network.validate()  
    return report




def printArgs(args):
    for k,v in args.items():
        print('------------------' + str(k) + '------------------\n')
        print(v)
        print('\n')