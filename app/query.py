from rdflib.plugins import sparql
from app.triple import Triple, setOfTriplesFromList
from app.tripleStore import TripleStore
from app.tripleStore import n3OfTripleSet
from rdflib import term

'''
Representation of a query.
Using the rdflib each query is parsed into an algebra term.
The Algebra Term is used to extract triples and used when executing a query over a local ConjunctivGraph.
'''
class Query:

    def __init__(self,in_query: str):
        self.query = in_query.replace(",","")
        self.parsed_query = sparql.processor.prepareQuery(self.query)
        self.triples = [Triple(*t) for t in self.extract_triples()]

    def extract_triples(self):
        list_of_triples = self.__extract_triples_rekursion(self.parsed_query.algebra)
        return list_of_triples

    def __extract_triples_rekursion(self, algebra: dict):
        result = []
        for k,v in algebra.items():
            if isinstance(v, dict):
                result = result + self.__extract_triples_rekursion(v)
            else:
                if k == 'triples':
                    result = result + v
        return result
    
    def __str__(self):
        return self.query

def constructQueryStringFrom(targetShape, initial_query_triples, path, shape_id):
    if targetShape != shape_id:
        where_clause = n3OfTripleSet(TripleStore(targetShape).getTriples().union(path).union(TripleStore(shape_id).getTriples()).union(initial_query_triples))
        query = 'CONSTRUCT {\n' + TripleStore(shape_id).n3() + '} WHERE {\n' + where_clause + '}'
    else:
        query = 'CONSTRUCT {\n' + n3OfTripleSet(TripleStore(targetShape).getTriples().union(initial_query_triples)) + '} WHERE {\n' + n3OfTripleSet(TripleStore(targetShape).getTriples().union(initial_query_triples)) + '}'
    return query
