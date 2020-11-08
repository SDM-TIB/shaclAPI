import itertools
from enum import Enum
import app.globals as globals
from rdflib.term import Variable

shapes_i = itertools.count()

def setShapeVariables(targetShape, shapes):
    for s in shapes:
        if s.id == targetShape:
            globals.shape_to_var[targetShape] = Variable('x')
        else:
            globals.shape_to_var[s.id] = Variable('s_' + str(next(shapes_i)))