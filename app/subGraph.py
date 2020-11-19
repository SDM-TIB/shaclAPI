import app.globals as globals
from rdflib.plugins.serializers.nquads import NQuadsSerializer
from rdflib import ConjunctiveGraph
import time
from app.triple import Triple
from rdflib.plugins.memory import IOMemory


'''
Representation of a local Subgraph.
The Subgraph is extended by the execution of construct queries over a given sparql endpoint.
Furthermore the Subgraph is queried every time travshacl needs information.

travshacl <--> Subgraph (local) <--> SPARQL Endpoint (web)
'''

ROW_LIMIT_PER_QUERY = 10000

def extendWithConstructQuery(query):
    print('\033[94m-------------------Extending Subgraph-------------------\033[00m')
    len_of_last_result = ROW_LIMIT_PER_QUERY
    triples_queried = 0
    while len_of_last_result >= ROW_LIMIT_PER_QUERY:
        new_query_string = str(query) + 'ORDER BY ASC(?x) LIMIT ' + str(ROW_LIMIT_PER_QUERY) + ' OFFSET ' + str(triples_queried)
        globals.endpoint.setQuery(new_query_string)
        try:
            print("\033[01mExecuting Construct Query: \033[0m")
            print('\033[02m' + new_query_string + '\033[0m\n')
            start = time.time()
            new_data_graph = globals.endpoint.query().convert()
            end = time.time()
            print("\033[01mExecution took " + str((end-start)*1000) + ' ms \033[0m')
        except Exception:
            print("Stopping Quering the External Graph because of an Error!")
            return False
        len_of_last_result = count(new_data_graph)
        print("\033[01mGot {} result triples \033[0m".format(len_of_last_result))
        #len_of_last_result = 2 # Just query 10000 results and not more --> comment out to query all
        triples_queried = triples_queried + len_of_last_result
        globals.subgraph = globals.subgraph + new_data_graph
    print('\033[94m-------------------------------------------------------------\033[00m')
    return True

def count(graph):
    result = 0
    for _ in graph.triples((None,None,None)):
        result = result + 1
    return result

def query(query, shape):
    #triples = query.triples
    return globals.subgraph.query(query.parsed_query)

def clear():
    globals.subgraphStore = IOMemory()
    globals.subgraph = ConjunctiveGraph(store=globals.subgraphStore)

#-------------------I/O Functions-------------------

def writeToFile(graph):
    with open("graph.nquads", "wb") as f:
        NQuadsSerializer(graph).serialize(f)

def readFromFile():
    g = ConjunctiveGraph()
    with open("graph.nquads", "rb") as f:
        g.parse(f, format="nquads")
        globals.subgraph = g
