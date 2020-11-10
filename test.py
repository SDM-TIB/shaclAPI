from rdflib import ConjunctiveGraph
from SPARQLWrapper import SPARQLWrapper
import time

query_string = '''
CONSTRUCT {
?x <http://dbpedia.org/ontology/imdbId> ?c_0x.
?x <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://dbpedia.org/ontology/Film>.
?x <http://dbpedia.org/ontology/starring> ?s_0.
} WHERE {
?x <http://dbpedia.org/ontology/imdbId> ?c_0x.
?x <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://dbpedia.org/ontology/Film>.
?x <http://dbpedia.org/ontology/starring> ?s_0.
} LIMIT 10000 OFFSET 0
'''
query = '''
PREFIX ub:<http://swat.cse.lehigh.edu/onto/univ-bench.owl#>
PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX dbo:<http://dbpedia.org/ontology/>
PREFIX dbr:<http://dbpedia.org/resource/>
PREFIX yago:<http://dbpedia.org/class/yago/>
PREFIX foaf:<http://xmlns.com/foaf/0.1/>
PREFIX :<http://example.org/>
SELECT DISTINCT ?x ?p_11 WHERE {
?x a dbo:Film. {
SELECT DISTINCT ?x ?p_11 WHERE {
?x dbo:starring ?p_11.
{
SELECT DISTINCT ?x WHERE {
?x dbo:imdbId ?p_8.
}
}}}} ORDER BY ?x
'''
print('Querying external:')
endpoint = SPARQLWrapper('http://dbpedia.org/sparql')
endpoint.setQuery(query_string)
graph = endpoint.query().convert()

start = time.time()
print('Querying internal')
result = graph.query(query)
end = time.time()
print('Done: ' + str(end- start))
json = result.serialize(encoding='utf-8',format='json')
