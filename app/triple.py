from rdflib.paths import InvPath
from rdflib.namespace import RDF
from rdflib.term import URIRef, Variable
from enum import IntEnum

class TripleE(IntEnum):
    SUBJECT = 0
    PREDICAT = 1
    OBJECT = 2

class Triple():
    def __init__(self, s, p, o, is_optional=False):
        self.optional = is_optional

        self.subject = s
        self.predicat = p
        self.object = o

    def __eq__(self, other) -> bool:
        return self.subject == other.subject and self.predicat == other.predicat and self.object == other.object and self.optional == other.optional

    def __iter__(self):  # This makes Triple behave as a Python Tuple Class Object
        yield self.subject
        yield self.predicat
        yield self.object

    @staticmethod
    def fromList(liste, is_optional):
        return [Triple(s, p, o, is_optional=is_optional) for (s, p, o) in liste]

    def toTuple(self, namespace_manager=None) -> str:
        subject_n3 = self.subject.n3(namespace_manager)
        if isinstance(self.predicat, InvPath):
            predicat_n3 = '^'+URIRef(self.predicat.arg).n3(namespace_manager)
        elif self.predicat == RDF.type and namespace_manager != None:
            predicat_n3 = 'a'
        else:
            predicat_n3 = self.predicat.n3(namespace_manager)
        object_n3 = self.object.n3(namespace_manager)

        return tuple([subject_n3, predicat_n3, object_n3])

    def __repr__(self) -> str:
        return str(tuple(self))

    def __str__(self) -> str:
        return self.n3()

    def __hash__(self):
        return hash(str(self.n3()))
