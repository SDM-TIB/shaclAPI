from rdflib import ConjunctiveGraph
from SPARQLWrapper import SPARQLWrapper

#Here is the place to store global Variables with Data needed for more then one Request.

#Used by subgraph.py
subgraph = ConjunctiveGraph()

#Used by tripleStore.py
seen_triples = set()

#Used by run.py
shape_network = None

#Used by subgraph.py - TODO: needs to be set properly in run.py
endpoint = SPARQLWrapper('http://dbpedia.org/sparql')

