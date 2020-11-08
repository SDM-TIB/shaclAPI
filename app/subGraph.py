import app.globals as globals
from rdflib.plugins.serializers.nquads import NQuadsSerializer
from rdflib import ConjunctiveGraph
import time
from app.triple import Triple

'''
Representation of a local Subgraph.
The Subgraph is extended by the execution of construct queries over a given sparql endpoint.
Furthermore the Subgraph is queried every time travshacl needs information.

travshacl <--> Subgraph (local) <--> SPARQL Endpoint (web)
'''

ROW_LIMIT_PER_QUERY = 10000

def extendWithConstructQuery(query_string):
    len_of_last_result = ROW_LIMIT_PER_QUERY
    triples_queried = 0
    while len_of_last_result >= ROW_LIMIT_PER_QUERY:
        new_query_string = query_string + ' LIMIT ' + str(ROW_LIMIT_PER_QUERY) + ' OFFSET ' + str(triples_queried)
        globals.endpoint.setQuery(new_query_string)
        print(new_query_string)
        try:
            print("Executing Construct Query: ")
            start = time.time()
            new_data_graph = globals.endpoint.query().convert()
            end = time.time()
            print("Execution took " + str(end-start) + 's')
        except Exception:
            return False
        len_of_last_result = count(new_data_graph)
        print(len_of_last_result)
        triples_queried = triples_queried + len_of_last_result
        globals.subgraph = globals.subgraph + new_data_graph
    return True
def count(graph):
    result = 0
    for _ in graph.triples((None,None,None)):
        result = result + 1
    return result

def query(query):
    return globals.subgraph.query(query)

def clear():
    globals.subgraph = ConjunctiveGraph(store=globals.subgraphStore)

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
    g = ConjunctiveGraph()
    with open("graph.nquads", "rb") as f:
        g.parse(f, format="nquads")
        globals.subgraph = g
