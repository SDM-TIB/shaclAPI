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
        return (self.subject == other.subject and self.predicat == other.predicat and self.object == other.object) or (self.subject == other.subject and self.predicat == other.predicat and type(self.object) == type(other.object) and self.optional == True and other.optional == True)
    
    def __hash__(self): #TODO: self.optional not used here
        return hash(str((str(self.subject.n3()),str(self.predicat.n3()),type(str(self.object.n3())))))
    
    def n3(self, optionals = False, prepending_point = True) -> str:
        if self.optional and optionals:
            return 'OPTIONAL{ ' + str(self.subject.n3()) + ' ' + str(self.predicat.n3()) + ' ' + str(self.object.n3()) + '. }'
        else:
            if prepending_point:
                return str(self.subject.n3()) + ' ' + str(self.predicat.n3()) + ' ' + str(self.object.n3()) + '.'
            else:
                return str(self.subject.n3()) + ' ' + str(self.predicat.n3()) + ' ' + str(self.object.n3())