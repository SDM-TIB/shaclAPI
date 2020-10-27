from rdflib.plugins import sparql
import app.globals as globals
from app.utils import printSet

class Query:

    def __init__(self,in_query):
        self.query = in_query.replace(",","")

    def extract_triples(self):
        parsed_query = sparql.processor.prepareQuery(self.query)
        list_of_triples = self.__extract_triples_rekursion(parsed_query.__dict__)
        print("Intersection: ")
        printSet(globals.seen_triples.intersection(set(list_of_triples)))
        globals.seen_triples = globals.seen_triples.union(set(list_of_triples))
        return list_of_triples

    def __extract_triples_rekursion(self,alg_dict):
        result = []
        #print('alg_dict: ' + str(alg_dict))
        for k,v in alg_dict.items():
            if isinstance(v, dict):
                #print('dict: ' + k)
                result = result + self.__extract_triples_rekursion(v)
                #print(result)
            else:
                #print('not_a_dict: ' + k)
                if k == 'triples':
                    result = result + v
                #print(result)
        return result

    def getSPARQL(self):
        return self.query

    def algebra(self):
        return sparql.processor.prepareQuery(self.query)
