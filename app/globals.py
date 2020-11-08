from rdflib import Graph, Namespace
from SPARQLWrapper import SPARQLWrapper
from rdflib.namespace import NamespaceManager
from rdflib.graph import Graph
from rdflib.plugins.memory import IOMemory

#Here is the place to store global Variables with Data needed for more then one Request.

#Used by subgraph.py
subgraphStore = IOMemory()
graphs = []
subgraph = Graph(store=subgraphStore)

#Used by tripleStore.py
tripleStorage = dict()

#Used by shapeGraph.py
shapeGraph = Graph()
namespaces = dict()
shapeNamespace = Namespace("http://example.org/shapes/")

#Used by subgraph.py
endpoint = None

#Used in run.py
network = None
referred_by = dict()
targetShape = None
shape_queried = dict()

#Used By variableStore
shape_to_var = dict()

initial_query = None

