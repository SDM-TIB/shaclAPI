from __future__ import annotations
import rdflib.term as term
import rdflib.paths as paths
from rdflib import Namespace

class Triple():
    '''
    A Triple is a triple of rdflib.terms.
    Triples are considered equal iff both triples have the same predicat and the same subject.
    '''

    def __init__(self, s, p, o):
        if isinstance(p, paths.InvPath):
            self.subject = o
            self.predicat = p.arg
            self.object = s
        else:
            self.subject = s
            self.predicat = p
            self.object = o

    def __str__(self) -> str:
        '''
        Returns a String Representation of the Triple
        '''
        return str((str(self.subject.n3()),str(self.predicat.n3()),str(self.object.n3())))

    '''
    Here we assume that a Triple equals another one iff the subject and the predicat is the same, this way we are ignoring different referring Object Variables in the Triple Store
    '''
    def __eq__(self, other) -> bool:
        return self.subject == other.subject and self.predicat == other.predicat and type(self.object) == type(other.object)
    
    def __hash__(self):
        return hash(str((str(self.subject.n3()),str(self.predicat.n3()),type(str(self.object.n3())))))
    
    def n3(self) -> str:
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