from flask import Flask, request, Response

from app.subgraph import Subgraph
from app.query import Query
import json

app = Flask(__name__)

@app.route("/endpoint", methods=['GET','POST'])
def endpoint():
    #Preprocessing of the Query
    if request.method == 'POST':
        printArgs(request.form)
        query = Query(request.form['query'])
    if request.method == 'GET':
        printArgs(request.args)
        query = Query(request.args['query'])

    query_triples = query.extract_triples()
    print("Number of triples: " + str(len(query_triples)))
    print("Triples: " + str(query_triples))

    #Get the internal subgraph
    subgraph = Subgraph()

    #Query the internal subgraph
    result = subgraph.query(query.getSPARQL())
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


#from rdflib.plugins.sparql.results.xmlresults import XMLResultParser
#def query_external_endpoint(query):
#    endpoint.setQuery(query)
#    result = endpoint.query().convert()
#    print(result)
#    return XMLResultParser.parse(result.toxml(encoding='utf-8'))

