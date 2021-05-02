import rdflib.term
from rdflib.paths import InvPath
from rdflib.namespace import RDF
from rdflib.term import URIRef, Variable
from enum import IntEnum

class TripleE(IntEnum):
    SUBJECT = 0
    PREDICAT = 1
    OBJECT = 2

class Triple():
    """
    Representation of a Triple, which consits of a subject, a predicate and an object. Additionally a triple can be marked as optional.
    Subject, predicat and objects need to be rdflib objects with n3() functions, which accept rdflib namespace_manager objects for shorting uris.
    """
    def __init__(self, s, p, o, is_optional=False):
        self.optional = is_optional

        self.subject = s
        self.predicat = p
        self.object = o

    def __eq__(self, other) -> bool:
        return self.subject == other.subject and self.predicat == other.predicat and self.object == other.object and self.optional == other.optional

    def __lt__(self, other) -> bool:
        if self.predicat == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type":
            if self.predicat != other.predicat:
                return True
            else:
                if isinstance(self.object, rdflib.term.Variable) and isinstance(other.object, rdflib.term.URIRef):
                    return False
                else:
                    return True
        elif isinstance(self.object, rdflib.term.URIRef):
            return True
        else:
            return False

    def __iter__(self):
        """
        This makes Triple behave similar to a Python Tuple Class Object
        """
        yield self.subject
        yield self.predicat
        yield self.object

    def __hash__(self):
        return hash((self.subject, self.predicat, self.object, self.optional))

    @staticmethod
    def fromList(liste, is_optional):
        """
        Transforms a list of python tuples to a list of Triples
        """
        return [Triple(s, p, o, is_optional=is_optional) for (s, p, o) in liste]

    def toTuple(self, namespace_manager=None) -> str:
        """
        Transforms a triple object into a Tuple
        """
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
