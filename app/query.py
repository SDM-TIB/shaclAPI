from rdflib.plugins import sparql

class Query:

    def __init__(self,in_query):
        self.query = in_query.replace(",","")

    def extract_triples(self):
        print(self.query)
        parsed_query = sparql.processor.prepareQuery(self.query)
        return self.__extract_triples_rekursion(parsed_query.__dict__)
        

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
