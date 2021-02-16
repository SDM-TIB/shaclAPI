import app.globals as globals
from app.triple import Triple
from rdflib import Graph
from rdflib import term
from rdflib import BNode
from rdflib.plugins.sparql import algebra
from rdflib.plugins.sparql.results.graph import GraphResultParser
import re
from travshacl.validation.Shape import Shape
from rdflib import Namespace

from typing import List


# Initalize with:
#   ShapeGraph.setPrefixes(initial_query.parsed_query.prologue.namespace_manager.namespaces())
#   ShapeGraph.constructAndSetGraphFromShapes(network.shapes)

# Needed globals:
#   shapeGraph = Graph()
#   namespaces = dict()


# Usage:
#   Extract Triples of the given Query to identify the mentioned Shape (?x --> s_id)
#   query_triples = query.triples()
#   possible_shapes = set()
#   for row in ShapeGraph.queryTriples(query_triples):
#       possible_shapes.add(ShapeGraph.uriRefToShapeId(row[0]))

shapeNamespace = Namespace("http://example.org/shapes/")

def setPrefixes(namespace):
    for name in namespace:
        globals.shapeGraph.bind(name[0],name[1])
    globals.namespaces = {key: value for (key,value) in [i for i in globals.shapeGraph.namespaces()]}

def constructAndSetGraphFromShapes(shapes: List[Shape]):
    print("\n------------------- Setting up ShapeGraph -------------------")
    namespaceURI = term.URIRef(str(shapeNamespace))

    globals.namespaces['shapes'] = namespaceURI
    globals.shapeGraph.bind('shapes', namespaceURI)

    for s in shapes:
        __addTargetDefinitionToGraph(s, shapeNamespace[str(s.id)])
    for s in shapes:
        __addReferencesToGraph(s, shapeNamespace[str(s.id)])
    for s in shapes:
        __addConstraintsToGraph(s, shapeNamespace[str(s.id)])

def queryTriples(triples: List[Triple]):
    query = 'SELECT ?x WHERE {\n'
    for triple in triples:
        query = query + triple.n3() + '\n'
    query = query + '}'
    return globals.shapeGraph.query(query)

def query(query):
    return globals.shapeGraph.query(query)

def extend(ref):
    # Returns a URI Ref
    t_inv = ref.startswith('^')
    t_split = ref.rfind(':')
    t_namespace = globals.namespaces[ref[t_inv:t_split]]
    t_path = ref[t_split+1:]
    path = Namespace(t_namespace)[t_path]
    if t_inv:
        result =  ~path
    else:
        result = path
    return result

def uriRefToShapeId(uri): #TODO: Fix hardcoeded Namepsace better use shapeNamespace above
    index = str(uri).rfind("shapes/")
    return str(uri)[index + 7:]

def clear():
    globals.shapeGraph = Graph()
    globals.namespaces = dict()

def __addReferencesToGraph(shape: Shape, targetNode: term.URIRef): #intershape constraints
    for obj,pred in shape.referencedShapes.items():
        new_triple = Triple(targetNode,extend(pred), shapeNamespace[obj])
        __addTripleToShapeGraph(new_triple)

def __addConstraintsToGraph(shape: Shape, targetNode: term.URIRef): #intrashape constraints
    for constraint in shape.constraints:
        if constraint.value != None:
            objNode = extend(constraint.value)
        else:
            objNode = BNode()
        new_triple = Triple(targetNode,extend(constraint.path), objNode)
        __addTripleToShapeGraph(new_triple)

def __addTargetDefinitionToGraph(shape: Shape, targetNode: term.URIRef):
    if shape.targetDef != None:
        new_triple = Triple(targetNode,term.URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'), extend(shape.targetDef))
        __addTripleToShapeGraph(new_triple)

def __addTripleToShapeGraph(new_triple: tuple):
    triple = new_triple.normalized(new_triple)
    new_triple = (triple.subject,triple.predicat,triple.object)
    if (not (new_triple[0],new_triple[1],None) in globals.shapeGraph) and (not (None, new_triple[1], new_triple[2]) in globals.shapeGraph):
        globals.shapeGraph.add(new_triple)
        print("Triple ADDED: " + str(new_triple))