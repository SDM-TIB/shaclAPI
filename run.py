from flask import Flask, request, Response
import rdflib
import sys
import os
import json
import logging
from SPARQLWrapper import SPARQLWrapper

sys.path.append('./travshacl')
from travshacl.validation.ShapeNetwork import ShapeNetwork
from travshacl.validation.core.ValidationTask import ValidationTask
from travshacl.validation.core.GraphTraversal import GraphTraversal
sys.path.remove('./travshacl')

from app.subgraph import Subgraph
from app.query import Query
from app.utils import printSet
from app.tripleStore import TripleStore
from app.triple import setOfTriplesFromList
import app.globals as globals
from app.shapeGraph import ShapeGraph

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.disabled = True

@app.route("/endpoint", methods=['GET','POST'])
def endpoint():
    #Preprocessing of the Query
    if request.method == 'POST':
        #printArgs(request.form)
        query = Query(request.form['query'])
    if request.method == 'GET':
        #printArgs(request.args)
        query = Query(request.args['query'])

    print("Query: ")
    print(str(query) + '\n')

    #Extract Triples of the given Query to identify the mentioned Shape (?x)
    query_triples = setOfTriplesFromList(query.extract_triples())

    possible_shapes = set()
    for row in ShapeGraph().queryTriples(query_triples):
        possible_shapes.add(ShapeGraph().uriRefToShapeId(row[0]))
    
    print('Possible Shapes:')
    print(possible_shapes)

    assert(len(possible_shapes) == 1)

    s_id = list(possible_shapes)[0]
    if len(globals.shape_to_var) == 0:
        globals.shape_to_var[s_id] = [rdflib.term.Variable('x')]

    print('s_id: ' + s_id)
    print(globals.referred_by)
    if s_id in globals.referred_by:
        for referrer in globals.referred_by[s_id]:
            print('Referred by ' + s_id + ' : ' + str(referrer))
            print('Content of Shape_to_Var: ' + str(globals.shape_to_var))
            if referrer['shape'] in globals.shape_to_var:
                subject_list = globals.shape_to_var[referrer['shape']]
                predicat = rdflib.term.URIRef(ShapeGraph().extend(referrer['pred']))
                matching_vars = []
                print("Triples seen: ")
                print(TripleStore())
                for s in subject_list:           
                    matching_vars = matching_vars + TripleStore().getObjectsWith(s,predicat)
                print('Matching var : ' + str(matching_vars))
                globals.shape_to_var[s_id] = matching_vars
    new_triples = set()
    print('shape_to_var :' + str(globals.shape_to_var[s_id]))
    for triple in query_triples:
        for var in globals.shape_to_var[s_id]:
            result_triple = triple.replaceX(var)
            new_triples.add(result_triple)

    print('New Triples :')
    for triple in new_triples:
        print(triple)
        
    #TODO: What is with multiple matching vars?
    #Construction of a new construct Query to update the internal subgraph
    construct_query = TripleStore().construct_query(new_triples)
    
    print("Construct Query: ")
    print(str(construct_query) + '\n')

    if construct_query != None:
        Subgraph().extendWithConstructQuery(construct_query)

    TripleStore().add(new_triples)

    #Query the internal subgraph with the given input query
    result = Subgraph().query(query.parsed_query)
    print("Number of triples seen: " + str(len(TripleStore())))
    print("Triples seen: ")
    print(TripleStore())
    print("Converting to json")
    print(len(result))
    json = result.serialize(encoding='utf-8',format='json')
    #print(dir(query.algebra()))
    print("-----------------------------------------------------------------")
    return Response(json, mimetype='application/json')

@app.route("/queryShapeGraph", methods = ['POST'])
def queryShapeGraph():
    query = Query(request.form['query'])
    result = ShapeGraph().query(query.parsed_query)
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
            - targetDef

    '''
    task_string = request.form['task']
    if task_string == 'g':
        task = ValidationTask.GRAPH_VALIDATION
    elif task_string == 's':
        task = ValidationTask.SHAPE_VALIDATION
    elif task_string == 't':
        task = ValidationTask.INSTANCES_VALID
    elif task_string == 'v':
        task = ValidationTask.INSTANCES_VIOLATION
    elif task_string == 'a':
        task = ValidationTask.ALL_INSTANCES
    else:
        return "Provide a valid Task String \{g,s,t,v,a\}"
    
    traversal_strategie_string = request.form['traversalStrategie']
    if traversal_strategie_string == "DFS":
        traversal_strategie = GraphTraversal.DFS
    elif traversal_strategie_string == "BFS":
        traversal_strategie = GraphTraversal.BFS
    else:
        return "Provide a valid traversal strategie string \{DFS,BFS\}"

    schema_directory = request.form['schemaDir']
    path = os.getcwd()
    os.makedirs(path + '/' + schema_directory, exist_ok=True)
    
    heuristics_string = request.form['heuristic']
    heuristics = parseHeuristics(heuristics_string)

    with open("config.json") as json_config_file:
        config = json.load(json_config_file)
    print(config['outputDirectory'])
    print(config['shapeFormat'])
    print(config['workInParallel'])
    print(config['useSelectiveQueries'])
    print(config['maxSplit'])
    print(config['ORDERBYinQueries'])
    print(config['SHACL2SPARQLorder'])
    print(config['external_endpoint'])

    internal_endpoint = "http://localhost:5000/endpoint"

    query = request.form['query']
    globals.query = query

    targetShape = request.form['targetShape']
    globals.targetShape = targetShape

    globals.endpoint = SPARQLWrapper(config['external_endpoint'])

    network = ShapeNetwork(schema_directory, config['shapeFormat'], internal_endpoint, traversal_strategie, task,
                            heuristics, config['useSelectiveQueries'], config['maxSplit'],
                            config['outputDirectory'], config['ORDERBYinQueries'], config['SHACL2SPARQLorder'], config['workInParallel'], query, targetShape)
    report = network.validate()  # run the evaluation of the SHACL constraints over the specified endpoint

    return report


def initalizeAPI(shapes):
    TripleStore().clear()
    Subgraph().clear()
    globals.referred_by = dict()

    #Read Input Query
    query = Query(globals.query)#TODO: extract Query

    #Set Prefixes of the ShapeGraph
    ShapeGraph().setPrefixes(query.parsed_query.prologue.namespace_manager.namespaces())
    
    #Step 1 + 2 integrated into travshacl

    #Create Dictionary to get a shape from a shape_id
    globals.shapes = {s.id: s for s in shapes}

    #Initalize the ShapeGraph with the given Shapes (including some duplicate elimination)
    ShapeGraph().constructAndSetGraphFromShapes(shapes)
    

    for s in shapes:
        for obj,pred in s.referencedShapes.items():
            if not obj in globals.referred_by:
                globals.referred_by[obj] = []
            globals.referred_by[obj].append({'shape': s.id, 'pred': pred})
    print(globals.referred_by)

    
    #Extract query_triples of the input query to construct a query such that the our Subgraph can be initalized
    query_triples = setOfTriplesFromList(query.extract_triples())
    construct_query = TripleStore().construct_query(query_triples)
    Subgraph().extendWithConstructQuery(construct_query)

    #And store queried triples
    TripleStore().add(query_triples)

    return "Done (/go)"
    


def parseHeuristics(input):
    heuristics = {}
    if not input:
        return heuristics
    if 'TARGET' in input:
        heuristics['target'] = True
    else:
        heuristics['target'] = False

    if 'IN' in input:
        heuristics['degree'] = 'in'
    elif 'OUT' in input:
        heuristics['degree'] = 'out'
    else:
        heuristics['degree'] = False
        
    if 'SMALL' in input:
        heuristics['properties'] = 'small'
    elif 'BIG' in input:
        heuristics['properties'] = 'big'
    else:
        heuristics['properties'] = False
    return heuristics

def printArgs(args):
    for k,v in args.items():
        print('------------------' + str(k) + '------------------\n')
        print(v)
        print('\n')