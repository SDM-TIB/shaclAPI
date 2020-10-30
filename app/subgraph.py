import app.globals as globals
from rdflib.plugins.serializers.nquads import NQuadsSerializer
from rdflib import ConjunctiveGraph
import time


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
        globals.subgraph = ConjunctiveGraph()

#-------------------I/O Functions-------------------
    def writeToFile(self):
        with open("graph.nquads", "wb") as f:
            NQuadsSerializer(globals.subgraph).serialize(f)

    def readFromFile(self):
        g = ConjunctiveGraph()
        with open("graph.nquads", "rb") as f:
            g.parse(f, format="nquads")
            globals.subgraph = g
