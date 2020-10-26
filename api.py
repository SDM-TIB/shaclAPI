from flask import Flask, request, Response
from SPARQLWrapper import SPARQLWrapper, XML
from rdflib import ConjunctiveGraph
from rdflib.plugins.serializers.nquads import NQuadsSerializer
from rdflib.plugins import sparql
from rdflib.plugins.sparql.results.xmlresults import XMLResultParser
import json

app = Flask(__name__)
endpoint = SPARQLWrapper('http://dbpedia.org/sparql')

@app.route("/endpoint", methods=['GET','POST'])
def querySubgraph():
    #Preprocessing of the Query
    if request.method == 'POST':
        printArgs(request.form)
        query = request.form['query']
    if request.method == 'GET':
        printArgs(request.args)
        query = request.args['query']
    query = query.replace(","," ")
    query_triples = extract_triples(query)
    print("Number of triples: " + str(len(query_triples)))
    print("Triples: " + str(query_triples))

    #Get the internal subgraph
    subgraph = getSubgraph()
    if subgraph == None:
        return "Set Construct Query first..." 

    #Query the internal subgraph
    result = subgraph.query(query)
    return Response(result.serialize(encoding='utf-8',format='json'), mimetype='application/json')

@app.route("/constructQuery", methods=['POST'])
def retrieveSubgraph():
    endpoint.setQuery(request.form['query'])
    setSubgraph(endpoint.query().convert())
    return "done\n"

def setSubgraph(subgraph):
    with open("graph.nquads", "wb") as f:
        NQuadsSerializer(subgraph).serialize(f)

def getSubgraph():
    g = ConjunctiveGraph()
    with open("graph.nquads", "rb") as f:
        g.parse(f, format="nquads")
    return g

def printArgs(args):
    for k,v in args.items():
        print('------------------' + str(k) + '------------------\n')
        print(v)
        print('\n')

def query_external_endpoint(query):
    endpoint.setQuery(query)
    result = endpoint.query().convert()
    print(result)
    return XMLResultParser.parse(result.toxml(encoding='utf-8'))

def extract_triples(query): 
    parsed_query = sparql.processor.prepareQuery(query)
    return rek_extract_triples(parsed_query.__dict__)
    

def rek_extract_triples(alg_dict):
    result = []
    #print('alg_dict: ' + str(alg_dict))
    for k,v in alg_dict.items():
        if isinstance(v, dict):
            #print('dict: ' + k)
            result = result + rek_extract_triples(v)
            #print(result)
        else:
            #print('not_a_dict: ' + k)
            if k == 'triples':
                result = result + v
            #print(result)
    return result
                

    

#def custom_evaluation_of_sparql(ctx,part):
#    print("Hello World")
#    print(str(ctx) + '\n' + str(part))
#    raise NotImplementedError

#sparql.CUSTOM_EVALS["test"] = custom_evaluation_of_sparql
