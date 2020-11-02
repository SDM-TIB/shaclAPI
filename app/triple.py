import rdflib.term as term
class Triple():
    
    def __init__(self, s, p, o):
        self.subject = s
        self.predicat = p
        self.object = o

    def __str__(self):
        return str((str(self.subject.n3()),str(self.predicat.n3()),str(self.object.n3())))
    
    def n3(self):
        return str(self.subject.n3()) + ' ' + str(self.predicat.n3()) + ' ' + str(self.object.n3()) + '.'
    
    def __eq__(self, other):
        return self.subject == other.subject and self.predicat == other.predicat #and self.object == other.object #ignoring Triples with different objects
    
    def __hash__(self):
        return hash(str((str(self.subject.n3()),str(self.predicat.n3()))))
    
    def replaceX(self,var):
        new_triple = self
        sub_typ = type(self.subject)
        pred_typ = type(self.predicat)
        obj_typ = type(self.object)
        if str(self.subject.n3()) == '?x':
            new_triple = Triple(sub_typ(var),pred_typ(self.predicat), obj_typ(self.object))
        if str(self.object.n3()) == '?x':
            new_triple = Triple(sub_typ(self.subject),pred_typ(self.predicat), obj_typ(var))
        return new_triple

def setOfTriplesFromList(liste):
    result = set()
    for triple in liste:
        result.add(Triple(triple[0],triple[1],triple[2]))
    return result
