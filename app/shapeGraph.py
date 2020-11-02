import app.globals as globals
from rdflib import ConjunctiveGraph
from rdflib import term


class ShapeGraph:
    def constructAndSetGraphFromShapes(self, shapes):
        for s in shapes:
            for obj,pred in s.referencedShapes.items():
                globals.shapeGraph.add((term.Literal(str(s.id)),term.URIRef(pred),term.Literal(obj)))
            #print(str(s.id) + ': ' + str(s.referencedShapes))
        for triple in globals.shapeGraph.triples((None,None,None)):
            print(triple[1].n3())

    def addSeenVariablesToGraph(self, triple):
        pass

    def setPrefixes(self, namespace):
        #print([ i for i in namespace])
        for name in namespace:
            globals.shapeGraph.bind(name[0],name[1])

    def clear(self):
        globals.shapeGraph = ConjunctiveGraph()