from rdflib.plugins import sparql
from app.triple import Triple
from app.tripleStore import TripleStore
from rdflib import term
import json
from rdflib.plugins.sparql.parserutils import CompValue

'''
Representation of a query.
Using the rdflib each query is parsed into an algebra term.
The Algebra Term is used to extract triples and used when executing a query over a local ConjunctivGraph.
'''
class Query:

    def __init__(self,in_query: str):
        self.query = in_query.replace(",","")
        self.__parsed_query = None
        self.__triples = None

    @property
    def parsed_query(self):
        if self.__parsed_query == None:
            self.__parsed_query = self.__parsed_query = sparql.processor.prepareQuery(self.query)
        return self.__parsed_query
    
    @property
    def triples(self):
        if self.__triples == None:
            self.__triples = [Triple(*t) for t in self.extract_triples()]
        return self.__triples

    @property
    def queriedVars(self):
        result = []
        try:
            result = self.parsed_query.algebra['PV']
        except Exception:
            pass
        finally:
            return result

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

    def dumpAlgebra(self,path):
        with open(path,'w') as f:
            json.dump(str(self.parsed_query.algebra),f, indent=1)
    
    def hasNoFilter(self):
        return self.__hasNoFilter(self.parsed_query.algebra)

    def __hasNoFilter(self,algebra: dict):
        result = True
        for k,v in algebra.items():
            if isinstance(v, CompValue) and v.name == 'Filter':
                return False
            elif isinstance(v, CompValue):
                result = result and self.__hasNoFilter(v)
        return result
    
    def simplify(self):
        if self.hasNoFilter():
            query_string = 'SELECT DISTINCT ' 
            for var in self.queriedVars:
                query_string = query_string + var.n3() + ' '
            query_string = query_string + 'WHERE {\n'
            for triple in self.triples:
                query_string = query_string + triple.n3() + '\n'
            query_string = query_string + '} ORDER BY ?x'
            return Query(query_string)
        else:
            return self


    @classmethod
    def constructQueryFrom(self,targetShape, initial_query_triples, path, shape_id):
        if targetShape != shape_id:
            where_clause = TripleStore.fromSet(TripleStore(targetShape).getTriples().union(path).union(TripleStore(shape_id).getTriples()).union(initial_query_triples)).n3()
            query = 'CONSTRUCT {\n' + TripleStore(shape_id).n3() + '} WHERE {\n' + where_clause + '}'
        else:
            query = 'CONSTRUCT {\n' + TripleStore.fromSet(TripleStore(targetShape).getTriples().union(initial_query_triples)).n3() + '} WHERE {\n' + TripleStore.fromSet(TripleStore(targetShape).getTriples().union(initial_query_triples)).n3() + '}'
        return self(query)
