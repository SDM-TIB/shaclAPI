from rdflib import Graph, Namespace, ConjunctiveGraph
from SPARQLWrapper import SPARQLWrapper
from rdflib.namespace import NamespaceManager
from rdflib.graph import Graph
from rdflib.plugins.memory import IOMemory

# Here is the place to store global Variables with Data needed for more then one Request.

# Used by subgraph.py
subgraphStore = IOMemory()
subgraph = ConjunctiveGraph(store=subgraphStore)
endpoint = None # Initalized by run.py in /go Route

# Used by tripleStore.py
tripleStorage = dict()

# Used by shapeGraph.py
shapeGraph = Graph()
namespaces = dict()
shapeNamespace = Namespace("http://example.org/shapes/")

# Used in run.py
network = None
targetShapeID = None
shape_queried = dict()
filter_clause = ''
ADVANCED_OUTPUT = False

# Used by variableStore
shape_to_var = dict()

# Used by path.py
referred_by = dict()


initial_query_triples = None

