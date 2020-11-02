from rdflib import ConjunctiveGraph
from SPARQLWrapper import SPARQLWrapper
from rdflib.namespace import NamespaceManager
from rdflib.graph import Graph

#Here is the place to store global Variables with Data needed for more then one Request.

#Used by subgraph.py
subgraph = ConjunctiveGraph()

#Used by tripleStore.py
seen_triples = set()

namespaceManager = None

#Used by shapeGraph.py
shapeGraph = ConjunctiveGraph()

#Used by subgraph.py - TODO: needs to be set properly in run.py
endpoint = SPARQLWrapper('http://dbpedia.org/sparql')


