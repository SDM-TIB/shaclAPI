import app.globals as globals
from app.utils import printSet

class TripleStore():

    def add(self, new_triples):
        globals.seen_triples = globals.seen_triples.union(set(new_triples))

    def intersection(self, with_triples):
        return globals.seen_triples.intersection(set(with_triples))
    
    def difference(self, with_triples):
        return set(with_triples).difference(globals.seen_triples)
    
    def getTriples(self):
        return globals.seen_triples
    
    def getObjectsWith(self, sub, pred):
        result = []
        for triple in globals.seen_triples:
            if triple.predicat.n3() == pred.n3() and triple.subject.n3() == sub.n3():
                result = result + [triple.object]
        return result

    
    def __len__(self):
        return len(globals.seen_triples)

    def __str__(self):
        result_str = ''
        for elem in globals.seen_triples:
            result_str = result_str + str(elem) + '\n'
        return result_str
    
    def construct_query(self, new_triples):
        not_seen_triples = self.difference(new_triples)
        if len(not_seen_triples) == 0:
            return None
        query = 'CONSTRUCT { \n'
        for triple in not_seen_triples:
                query = query + triple.n3() + '\n'
        query = query + '} WHERE { \n'
        for triple in self.getTriples().union(new_triples):
            query = query + triple.n3() + '\n'
        query = query + '}'
        return query
    
    def clear(self):
        globals.seen_triples = set()