from __future__ import annotations
import rdflib.term as term

class Triple():
    '''
    A Triple is a triple of rdflib.terms.
    Triples are considered equal iff both triples have the same predicat and the same subject.
    '''

    def __init__(self, s, p, o):
        self.subject = s
        self.predicat = p
        self.object = o

    def __str__(self) -> str:
        return str((str(self.subject.n3()),str(self.predicat.n3()),str(self.object.n3())))

    def __eq__(self, other) -> bool:
        return self.subject == other.subject and self.predicat == other.predicat
    
    def __hash__(self):
        return hash(str((str(self.subject.n3()),str(self.predicat.n3()))))
    
    def n3(self) -> str:
        if self.predicat.n3().startswith('^'):
            return str(self.object.n3()) + ' ' + str(self.predicat.n3())[1:] + ' ' + str(self.subject.n3()) + '.' 
        return str(self.subject.n3()) + ' ' + str(self.predicat.n3()) + ' ' + str(self.object.n3()) + '.'
    
    def replaceX(self,var: term.Variable) -> Triple:
        '''
        Here we replace each ?x with the specified variable var (rdflib.term.Variable).
        '''
        new_triple = self
        if str(self.subject.n3()) == '?x':
            new_triple = Triple(var,self.predicat, self.object)
        if str(self.object.n3()) == '?x':
            new_triple = Triple(self.subject,self.predicat, var)
        return new_triple

def setOfTriplesFromList(liste: list(Triple)):
    result = set()
    for triple in liste:
        result.add(Triple(triple[0],triple[1],triple[2]))
    return result
