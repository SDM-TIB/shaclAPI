import itertools
from enum import Enum
import app.globals as globals
from rdflib.term import Variable

shapes_i = itertools.count()

# Needed globals:
#   shape_to_var = dict()

# Initalize with:
#   VariableStore.setShapeVariables(globals.targetShapeID, network.shapes)

def setShapeVariables(targetShapeID, shapes):
    for s in shapes:
        if s.id == targetShapeID:
            globals.shape_to_var[targetShapeID] = Variable('x')
        else:
            globals.shape_to_var[s.id] = Variable('s_' + str(next(shapes_i)))

def shape_to_var(shape_id):
    return globals.shape_to_var[shape_id]