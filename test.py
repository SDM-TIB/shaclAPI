from rdflib import ConjunctiveGraph
from rdflib.term import URIRef
from SPARQLWrapper import SPARQLWrapper
import time
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from requests.auth import HTTPDigestAuth

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

AUTH_USER = 'dba' # Default Virtuoso username
AUTH_PASS = 'dba' # Default Virtuoso password
def_identifier = URIRef("http://www.example.com/my-graph")
store = SPARQLUpdateStore(queryEndpoint='http://localhost:8890/sparql', auth=HTTPDigestAuth(AUTH_USER,AUTH_PASS),context_aware=True,
                              postAsEncoded=False, update_endpoint='http://localhost:8890/sparql-auth')

g = ConjunctiveGraph(store=store,identifier=def_identifier)
g.addN([(s,p,o,def_identifier) for (s,p,o) in graph.triples((None,None,None))])
store.add_graph(g)

start = time.time()
print('Querying internal')
result = store.query(query)

json = result.serialize(encoding='utf-8',format='json')
end = time.time()
print('Done: ' + str(end- start))
#print(json)
