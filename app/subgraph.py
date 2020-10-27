import app.globals as globals
from rdflib.plugins.serializers.nquads import NQuadsSerializer

class Subgraph:
    def extendWithConstructQuery(self,query):
        globals.endpoint.setQuery(query)
        try:
            new_data_graph = globals.endpoint.query().convert()
        except Exception:
            return False
        globals.subgraph = globals.subgraph + new_data_graph    
        return True
    
    def query(self,query):
        return globals.subgraph.query(query)

#-------------------I/O Functions-------------------
    def writeToFile(self):
        with open("graph.nquads", "wb") as f:
            NQuadsSerializer(globals.subgraph).serialize(f)

    def readFromFile(self):
        g = ConjunctiveGraph()
        with open("graph.nquads", "rb") as f:
            g.parse(f, format="nquads")
            globals.subgraph = g
