import app.globals as globals
from app.triple import Triple
from rdflib.term import URIRef
from app.shapeGraph import extend

def computeReferredByDictionary(shapes):
    for s in shapes:
        for obj,pred in s.referencedShapes.items():
            if not obj in globals.referred_by:
                globals.referred_by[obj] = []
            globals.referred_by[obj].append({'shape': s.id, 'pred': pred})

def clearReferredByDictionary():
    globals.referred_by = dict()

def computePathsToTargetShape(shape_id, path):
    if globals.targetShape == shape_id:
        return [path]
    else:
        stack = globals.referred_by[shape_id].copy()
        result = []
        while len(stack) != 0:
            actual_path = path.copy()
            referrer = stack.pop()
            if referrer['pred'].startswith('^'):
                actual_path.append(Triple(globals.shape_to_var[shape_id],URIRef(extend(referrer['pred'])),globals.shape_to_var[referrer['shape']]))
            else:
                actual_path.append(Triple(globals.shape_to_var[referrer['shape']],URIRef(extend(referrer['pred'])), globals.shape_to_var[shape_id]))
            #actual_path.append({'shape_from': referrer['shape'], 'pred': referrer['pred'], 'shape_to': shape_id})
            result = result + computePathsToTargetShape(referrer['shape'],actual_path)
        return result
