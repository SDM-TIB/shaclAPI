import app.globals as globals
from rdflib.plugins.serializers.nquads import NQuadsSerializer
from rdflib import Graph
import time
from app.triple import Triple

'''
Representation of a local Subgraph.
The Subgraph is extended by the execution of construct queries over a given sparql endpoint.
Furthermore the Subgraph is queried every time travshacl needs information.

travshacl <--> Subgraph (local) <--> SPARQL Endpoint (web)
'''

def extendWithConstructQuery(query_string):
    globals.endpoint.setQuery(query_string)
    try:
        print("Executing Construct Query: ")
        start = time.time()
        new_data_graph = globals.endpoint.query().convert()
        end = time.time()
        print("Execution took " + str(end-start) + 's')
    except Exception:
        return False
    globals.subgraph = globals.subgraph + new_data_graph
    return True

def query(query):
    return globals.subgraph.query(query)

def clear():
    globals.subgraph = Graph()

#-------------------I/O Functions-------------------
'''
TODO: Warum funktioniert das Speichern und Laden des Subgraphen nicht mehr?
'''
def writeToFile(graph):
    for s, p , o in graph.triples((None,None,None)):
        print(Triple(s, p, o))
    #with open("graph.nquads", "wb") as f:
    #    NQuadsSerializer(graph).serialize(f)

def readFromFile():
    g = Graph()
    with open("graph.nquads", "rb") as f:
        g.parse(f, format="nquads")
        globals.subgraph = g
