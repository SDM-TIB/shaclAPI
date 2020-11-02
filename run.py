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
        possible_shapes.add(ShapeGraph().uriRefToShape(row[0]))
    
    #TODO: Match variables in triples to internal variables

    #Construction of a new construct Query to update the internal subgraph
    construct_query = TripleStore().construct_query(query_triples)
    
    print("Construct Query: ")
    print(str(construct_query) + '\n')

    if construct_query != None:
        Subgraph().extendWithConstructQuery(construct_query)

    TripleStore().add(query_triples)

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