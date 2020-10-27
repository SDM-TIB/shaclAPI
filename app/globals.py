from rdflib import ConjunctiveGraph
from SPARQLWrapper import SPARQLWrapper

#List of global variables
subgraph = ConjunctiveGraph()
endpoint = SPARQLWrapper('http://dbpedia.org/sparql')
seen_triples = set()
