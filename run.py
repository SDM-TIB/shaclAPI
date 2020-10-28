from flask import Flask, request, Response

from app.subgraph import Subgraph
from app.query import Query
import json
import logging
from app.utils import printSet
from app.tripleStore import TripleStore

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

    #print("Query: " + str(query.getSPARQL()))

    query_triples = query.extract_triples()
    #print("Number of triples in actual query: " + str(len(query_triples)))

    print("Intersection: ")
    printSet(TripleStore().intersection(query_triples))

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
        return "done\n"
    else:
        return "An Error with the query occured!"

def printArgs(args):
    for k,v in args.items():
        print('------------------' + str(k) + '------------------\n')
        print(v)
        print('\n')