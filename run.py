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

    query_triples = setOfTriplesFromList(query.extract_triples())
    #print("Number of triples in actual query: " + str(len(query_triples)))

    print("Intersection: ")
    printSet(TripleStore().intersection(query_triples))

    print("Construct Query: ")
    construct_query = TripleStore().construct_query(query_triples)
    print(str(construct_query) + '\n')

    if construct_query != None:
        Subgraph().extendWithConstructQuery(construct_query)

    TripleStore().add(query_triples)
    #Query the internal subgraph
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

@app.route("/go", methods=['POST'])
def run():
    TripleStore().clear()
    Subgraph().clear()

    query = Query(request.form['query'])
    print('starshaped Query: ')
    print(query)

    #Set Prefixes of the ShapeGraph
    globals.namespaceStorage = query.parsed_query.prologue.namespace_manager
    ShapeGraph().setPrefixes(query.parsed_query.prologue.namespace_manager.namespaces())
    
    #Step 1 + 2
    parsed_query = parse_query(str(query))
    shapes = reduce_shape_network(request.form['shape_dir'],parsed_query,GraphTraversal.DFS)
    ShapeGraph().constructAndSetGraphFromShapes(shapes)

    query_triples = setOfTriplesFromList(query.extract_triples())
    
    #Create Local Subgraph from given Query
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