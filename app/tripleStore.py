import app.globals as globals
from app.utils import printSet
from rdflib import term
from app.triple import Triple
from app.utils import extend

class TripleStore():
    '''
    TripleStore can be seen as a Storage Manager for various Set of Triples of rdflib.term Representations.
    Furthermore TripleStore is able to create CONSTRUCT Queries given a new Set of Triples to extend the Subgraph.
    '''
    def __init__(self,name):
        self.name = name
        if not self.name in globals.tripleStorage:
            globals.tripleStorage[self.name] = set()

    def add(self, new_triples):
        globals.tripleStorage[self.name] = globals.tripleStorage[self.name].union(set(new_triples))

    def remove(self, triple):
        globals.tripleStorage[self.name].remove(triple)

    def intersection(self, with_triples):
        return globals.tripleStorage[self.name].intersection(set(with_triples))
    
    def difference(self, with_triples):
        return set(with_triples).difference(globals.tripleStorage[self.name])
    
    def getTriples(self):
        return globals.tripleStorage[self.name]
    
    def getTriplesWith(self, sub, pred):
        result = []
        for triple in globals.tripleStorage[self.name]:
            if triple.predicat.n3() == pred.n3() and triple.subject.n3() == sub.n3():
                result = result + [triple]
        return result
    
    def getTriplesReferingToVar(self,var):
        result = []
        for triple in globals.tripleStorage[self.name]:
            if triple.object.n3() == var.n3() or triple.subject.n3() == var.n3():
                result = result + [triple]
        return result

    def __len__(self):
        return len(globals.tripleStorage[self.name])

    def __str__(self):
        result_str = ''
        for elem in globals.tripleStorage[self.name]:
            result_str = result_str + str(elem) + '\n'
        return result_str
    
    def n3(self):
        result = ""
        for triple in globals.tripleStorage[self.name]:
            result = result + triple.n3() + '\n'
        return result
        
    def clear(self):
        globals.tripleStorage[self.name] = set()

    @classmethod
    def fromShape(self,shape):
        store = self(shape.id)
        store.clear()

        constraint_triple_set = set()

        for constraint, i in zip(shape.constraints, range(len(shape.constraints))):
            if constraint.value != None: 
                # In that case we have an URI given
                objNode = term.URIRef(extend(constraint.value))
            elif constraint.shapeRef != None:
                # In that case we eventually have to reuse a variable...TODO: That's not always correct here loops!
                objNode = globals.shape_to_var[constraint.shapeRef]
            else:
                # Not further specified constraint
                objNode  = term.Variable('c_' + str(i) + globals.shape_to_var[shape.id])

            if constraint.path.startswith('^'):
                constraint_triple_set.add(Triple(objNode,term.URIRef(extend(constraint.path[1:])), globals.shape_to_var[shape.id]))
            else:
                constraint_triple_set.add(Triple(globals.shape_to_var[shape.id],term.URIRef(extend(constraint.path)), objNode))

        if shape.targetDef != None:
            constraint_triple_set.add(Triple(globals.shape_to_var[shape.id],term.URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'), term.URIRef(extend(shape.targetDef))))
        store.add(constraint_triple_set)
        return store 

    @classmethod
    def fromSet(self,triple_set, name = 'temp'):
        store = self(name)
        store.clear()
        store.add(triple_set)
        return store