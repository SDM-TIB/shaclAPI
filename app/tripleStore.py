import app.globals as globals

class TripleStore():

    def add(self, new_triples):
        globals.seen_triples = globals.seen_triples.union(set(new_triples))

    def intersection(self, with_triples):
        return globals.seen_triples.intersection(set(with_triples))
    
    def getTriples(self):
        return globals.seen_triples
    
    def __len__(self):
        return len(globals.seen_triples)

    def __str__(self):
        result_str = ''
        for elem in globals.seen_triples:
            result_str = result_str + str((str(elem[0].n3()),str(elem[1].n3()),str(elem[2].n3()))) + '\n'
        return result_str
