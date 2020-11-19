import app.globals as globals
from app.triple import Triple
from rdflib.term import URIRef
from app.utils import extend

def computePathsToTargetShape(shape_id, path):
    if globals.targetShape == shape_id:
        return [path]
    else:
        stack = globals.referred_by[shape_id].copy()
        result = []
        while len(stack) != 0:
            actual_path = path.copy()
            referrer = stack.pop()
            actual_path.append(Triple(globals.shape_to_var[referrer['shape']],URIRef(extend(referrer['pred'])), globals.shape_to_var[shape_id]))
            #actual_path.append({'shape_from': referrer['shape'], 'pred': referrer['pred'], 'shape_to': shape_id})
            result = result + computePathsToTargetShape(referrer['shape'],actual_path)
        return result
