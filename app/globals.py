from rdflib import Graph, Namespace
from SPARQLWrapper import SPARQLWrapper
from rdflib.namespace import NamespaceManager
from rdflib.graph import Graph

#Here is the place to store global Variables with Data needed for more then one Request.

#Used by subgraph.py
subgraph = Graph()

#Used by tripleStore.py
tripleStorage = dict()

#Used by shapeGraph.py
shapeGraph = Graph()
namespaces = dict()
shapeNamespace = Namespace("http://example.org/shapes/")


#Used by subgraph.py - TODO: needs to be set properly in run.py
endpoint = None

network = None
referrd_by = dict()
shape_to_var = dict()
targetShape = None

