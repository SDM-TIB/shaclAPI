class Triple():
    def __init__(self, s, p, o, is_optional = False):
        self.optional = is_optional

        self.subject = s
        self.predicat = p
        self.object = o

    def __eq__(self, other) -> bool:
        return self.subject == other.subject and self.predicat == other.predicat and self.object == other.object and self.optional == other.optional
    
    def __iter__(self): # This makes Triple behave as a Python Tuple Class Object
        yield self.subject
        yield self.predicat
        yield self.object
    
    @staticmethod
    def fromList(liste, is_optional):
        return [Triple(s,p,o, is_optional= is_optional) for (s,p,o) in liste]
