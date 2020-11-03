import app.globals as globals
from rdflib.plugins.serializers.nquads import NQuadsSerializer
from rdflib import Graph
import time

'''
Representation of a local Subgraph.
The Subgraph is extended by the execution of construct queries over a given sparql endpoint.
Furthermore the Subgraph is queried every time travshacl needs information.

travshacl <--> Subgraph (local) <--> SPARQL Endpoint (web)
'''

class Subgraph:
    def extendWithConstructQuery(self,query_string):
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
    
    def query(self,query):
        return globals.subgraph.query(query)
    
    def clear(self):
        globals.subgraph = Graph()

#-------------------I/O Functions-------------------
    def writeToFile(self):
        with open("graph.nquads", "wb") as f:
            NQuadsSerializer(globals.subgraph).serialize(f)

    def readFromFile(self):
        g = Graph()
        with open("graph.nquads", "rb") as f:
            g.parse(f, format="nquads")
            globals.subgraph = g
