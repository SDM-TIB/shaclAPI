from flask import Flask, request
from SPARQLWrapper import SPARQLWrapper
from rdflib import ConjunctiveGraph
from rdflib.plugins.serializers.nquads import NQuadsSerializer
import json

app = Flask(__name__)
endpoint = SPARQLWrapper('http://dbpedia.org/sparql')

@app.route("/endpoint", methods=['POST'])
def querySubgraph():
    subgraph = getSubgraph()
    if subgraph == None:
        return "Set Construct Query first..."    
    result = subgraph.query(request.form['query'])
    return result.serialize(encoding='utf-8',format='json')

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
    




