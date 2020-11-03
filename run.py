from flask import Flask, request, Response

from app.subgraph import Subgraph
from app.query import Query
import json
import logging
from app.utils import printSet
from app.tripleStore import TripleStore
from app.triple import setOfTriplesFromList
from query_parser import parse_query, reduce_shape_network
import app.globals as globals
import sys
import rdflib

sys.path.append('./travshacl')
from travshacl.validation.core.GraphTraversal import GraphTraversal
sys.path.remove('./travshacl')

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

    #print(dir(query.algebra()))
    print("-----------------------------------------------------------------")
    return Response(result.serialize(encoding='utf-8',format='json'), mimetype='application/json')

@app.route("/constructQuery", methods=['POST'])
def setInitialSubgraph():
    subgraph = Subgraph()
    if subgraph.extendWithConstructQuery(request.form['query']):
        return "Done (/constructQuery)\n"
    else:
        return "An Error with the query occured!"

@app.route("/queryShapeGraph", methods = ['POST'])
def queryShapeGraph():
    query = Query(request.form['query'])
    result = ShapeGraph().query(query.parsed_query)
    for row in result:
        print(row)
    return "Done"
    

@app.route("/go", methods=['POST'])
def run():
    TripleStore().clear()
    Subgraph().clear()
    globals.referred_by = dict()

    #Read Input Query
    query = Query(request.form['query'])

    #Set Prefixes of the ShapeGraph
    ShapeGraph().setPrefixes(query.parsed_query.prologue.namespace_manager.namespaces())
    
    #Step 1 + 2
    parsed_query = parse_query(str(query))
    shapes = reduce_shape_network(request.form['shape_dir'],parsed_query,GraphTraversal.DFS)

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
    




def printArgs(args):
    for k,v in args.items():
        print('------------------' + str(k) + '------------------\n')
        print(v)
        print('\n')