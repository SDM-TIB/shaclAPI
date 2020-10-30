from rdflib.plugins import sparql

class Query:

    def __init__(self,in_query):
        self.query = in_query.replace(",","")
        self.parsed_query = sparql.processor.prepareQuery(self.query)

    def extract_triples(self):
        #Call Rekursion
        list_of_triples = self.__extract_triples_rekursion(self.parsed_query.algebra)
        return list_of_triples

    def __extract_triples_rekursion(self,alg_dict):
        result = []
        for k,v in alg_dict.items():
            if isinstance(v, dict):
                result = result + self.__extract_triples_rekursion(v)
            else:
                if k == 'triples':
                    result = result + v
        return result

    def getSPARQL(self):
        return self.query
    
    def __str__(self):
        return self.query
