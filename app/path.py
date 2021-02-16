import app.globals as globals
from app.triple import Triple
from rdflib.term import URIRef
from app.shapeGraph import extend
from app.utils import printSet
import app.variableStore as VariableStore

# Needed globals:
#   referred_by = dict()

# Usage:
#   Extract Pathes from the Target Shape (target_shape_id) to the identified Shape (s_id)
#   paths = Path.computePathsToTargetShape(target_shape_id, s_id,[])


def computeReferredByDictionary(shapes):
    for s in shapes:
        for obj,pred in s.referencedShapes.items():
            if not obj in globals.referred_by:
                globals.referred_by[obj] = []
            globals.referred_by[obj].append({'shape': s.id, 'pred': pred})

def clearReferredByDictionary():
    globals.referred_by = dict()

def computePathsToTargetShape(target_shape_id, shape_id, path):
    '''
    Returns a List with Lists of Triples representing the paths from the targetShape to the shape_id
    '''
    if target_shape_id == shape_id:
        return [path]
    else:
        stack = globals.referred_by[shape_id].copy()
        result = []
        while len(stack) != 0:
            actual_path = path.copy()
            referrer = stack.pop()
            actual_path.append(Triple(VariableStore.shape_to_var(referrer['shape']),extend(referrer['pred']), VariableStore.shape_to_var(shape_id)))
            result = result + computePathsToTargetShape(target_shape_id, referrer['shape'],actual_path)
        return result

def pathToAbbreviatedString(path):
    path.reverse()
    printSet(path)
    assert len(path) >= 1, 'Path must be longer then zero!'
    result = path[0].subject.n3() + ' '
    for triple in path:
        result = result + triple.predicat.n3() + '/'
    result = result[0:-1] + ' ' + path[-1].object.n3() + '.\n'
    return result