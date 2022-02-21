import rdflib.term
from rdflib.paths import InvPath
from rdflib.namespace import RDF
from rdflib.term import URIRef
from enum import IntEnum


class TripleE(IntEnum):
    SUBJECT = 0
    PREDICATE = 1
    OBJECT = 2


class Triple:
    """
    Representation of a Triple, which consists of a subject, a predicate and an object.
    Additionally a triple can be marked as optional.
    Subject, predicate and objects need to be rdflib objects with n3() functions, which accept
    rdflib namespace_manager objects for shortening URIs.
    """
    def __init__(self, s, p, o, is_optional=False):
        self.optional = is_optional

        self.subject = s
        self.predicate = p
        self.object = o

    def __eq__(self, other) -> bool:
        return self.subject == other.subject and \
            self.predicate == other.predicate and \
            self.object == other.object and \
            self.optional == other.optional

    def __lt__(self, other) -> bool:
        if self.predicate == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type" or self.predicate == "a":
            if isinstance(self.object, rdflib.term.URIRef):
                return True
            elif self.predicate == other.predicate and isinstance(other.object, rdflib.term.URIRef):
                return False
        elif isinstance(self.predicate, rdflib.term.URIRef) and isinstance(self.object, rdflib.term.URIRef):
            return True
        else:
            return False

    def __iter__(self):
        """
        This makes Triple behave similar to a Python Tuple Class Object
        """
        yield self.subject
        yield self.predicate
        yield self.object

    def __hash__(self):
        return hash((self.subject, self.predicate, self.object, self.optional))

    @staticmethod
    def fromList(list_, is_optional):
        """
        Transforms a list of python tuples to a list of Triples
        """
        return [Triple(s, p, o, is_optional=is_optional) for (s, p, o) in list_]

    def toTuple(self, namespace_manager=None) -> tuple:
        """
        Transforms a triple object into a Tuple
        """
        subject_n3 = self.subject.n3(namespace_manager)
        if isinstance(self.predicate, InvPath):
            predicate_n3 = '^'+URIRef(self.predicate.arg).n3(namespace_manager)
        elif self.predicate == RDF.type and namespace_manager is not None:
            predicate_n3 = 'a'
        else:
            predicate_n3 = self.predicate.n3(namespace_manager)
        object_n3 = self.object.n3(namespace_manager)

        return tuple([subject_n3, predicate_n3, object_n3])

    def n3(self, namespace_manager=None) -> str:
        (subject_n3, predicate_n3, object_n3) = self.toTuple(namespace_manager)
        if self.optional:
            return 'OPTIONAL{ ' + subject_n3 + ' ' + predicate_n3 + ' ' + object_n3 + ' }'
        else:
            return subject_n3 + ' ' + predicate_n3 + ' ' + object_n3 + '.'
    
    def set_subject(self, s):
        self.subject = s
        return self

    def __repr__(self) -> str:
        return str(tuple(self))
