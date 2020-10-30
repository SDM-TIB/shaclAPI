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
        return hash(str(self))

def setOfTriplesFromList(liste):
    result = set()
    for triple in liste:
        result.add(Triple(triple[0],triple[1],triple[2]))
    return result
