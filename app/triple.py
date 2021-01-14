from __future__ import annotations
import rdflib.term as term
import rdflib.paths as paths
from rdflib import Namespace

class Triple():
    '''
    A Triple is a triple of rdflib.terms.
    Triples are considered equal iff both triples have the same subject, predicate and the same object type.
    '''

    def __init__(self, s, p, o, optional = False):
        self.optional = optional
        self.isInvPath = isinstance(p, paths.InvPath)

        self.subject = s
        self.predicat = p
        self.object = o
    
    @classmethod
    def normalized(self,triple):
        if triple.isInvPath:
            return self(triple.object,triple.predicat.arg,triple.subject)
        return triple

    def __str__(self) -> str:
        '''
        Returns a String Representation of the Triple
        '''
        triple_string = str((str(self.subject.n3()),str(self.predicat.n3()),str(self.object.n3())))

        if self.optional:
            return 'OPTIONAL ' + triple_string
        else:
            return triple_string

    def __eq__(self, other) -> bool: #TODO: self.optional not used here
        return self.subject == other.subject and self.predicat == other.predicat and self.object == other.object
    
    def __hash__(self): #TODO: self.optional not used here
        return hash(str((str(self.subject.n3()),str(self.predicat.n3()),type(str(self.object.n3())))))
    
    def n3(self, optionals = False) -> str:
        if self.optional and optionals:
            return 'OPTIONAL{ ' + str(self.subject.n3()) + ' ' + str(self.predicat.n3()) + ' ' + str(self.object.n3()) + '. }'
        else:
            return str(self.subject.n3()) + ' ' + str(self.predicat.n3()) + ' ' + str(self.object.n3()) + '.'
    
    
    # def replaceX(self,var: term.Variable) -> Triple:
    #     '''
    #     Here we replace each ?x with the specified variable var (rdflib.term.Variable).
    #     '''
    #     new_triple = self
    #     if str(self.subject.n3()) == '?x':
    #         new_triple = Triple(var,self.predicat, self.object)
    #     if str(self.object.n3()) == '?x':
    #         new_triple = Triple(self.subject,self.predicat, var)
    #     return new_triple