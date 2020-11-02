import app.globals as globals
from rdflib import ConjunctiveGraph
from rdflib import term
from rdflib import BNode
from rdflib.plugins.sparql.results.graph import GraphResultParser
import re



class ShapeGraph:
    def constructAndSetGraphFromShapes(self, shapes):
        namespaceURI = term.URIRef(str(globals.shapeNamespace))
        globals.namespaces['shapes'] = namespaceURI
        globals.shapeGraph.bind('shapes', namespaceURI)
        for s in shapes:
            self.addTargetDefinitionToGraph(s, globals.shapeNamespace[str(s.id)])
        for s in shapes:
            self.addReferencesToGraph(s, globals.shapeNamespace[str(s.id)])
        for s in shapes:
            self.addConstraintsToGraph(s, globals.shapeNamespace[str(s.id)])
                
        #for triple in globals.shapeGraph.triples((None,None,None)):
        #    print(triple)

    def addReferencesToGraph(self, shape, targetNode):
        for obj,pred in shape.referencedShapes.items():
            new_triple = (targetNode,term.URIRef(self.extend(pred)),globals.shapeNamespace[obj])
            self.addTripleToShapeGraph(new_triple)

    def addConstraintsToGraph(self, shape, targetNode):
        for constraint in shape.constraints:
            if constraint.value != None:
                objNode = term.URIRef(self.extend(constraint.value))
            else:
                objNode = BNode()
            if constraint.path.startswith('^'):
                new_triple = (objNode,term.URIRef(self.extend(constraint.path[1:])), targetNode)
            else:
                new_triple = (targetNode,term.URIRef(self.extend(constraint.path)), objNode)
            self.addTripleToShapeGraph(new_triple)
    
    def addTargetDefinitionToGraph(self, shape, targetNode):
        if shape.targetDef != None:
            new_triple = (targetNode,term.URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'), term.URIRef(self.extend(shape.targetDef)))
            self.addTripleToShapeGraph(new_triple)

    def addTripleToShapeGraph(self, new_triple):
        if (not (new_triple[0],new_triple[1],None) in globals.shapeGraph) and (not (None, new_triple[1], new_triple[2]) in globals.shapeGraph):
            globals.shapeGraph.add(new_triple)
            print("Triple ADDED: " + str(new_triple))


    def queryTriples(self, triples):
        query = 'SELECT ?x WHERE {\n'
        for triple in triples:
            query = query + triple.n3() + '\n'
        query = query + '}'

        print('ShapeGraph Query:')
        print(query)

        return globals.shapeGraph.query(query)

    def query(self, query):
        return globals.shapeGraph.query(query)

    def setPrefixes(self, namespace):
        #print([ i for i in namespace])
        for name in namespace:
            globals.shapeGraph.bind(name[0],name[1])
        globals.namespaces = {key: value for (key,value) in [i for i in globals.shapeGraph.namespaces()]}

    def extend(self, term):
        index = term.rfind(":")
        extended_term = str(globals.namespaces[term[:index]]) + term[index+1:]
        return extended_term
    
    def uriRefToShapeId(self, uri):
        index = str(uri).rfind("shapes/")
        return str(uri)[index + 7:]

    def clear(self):
        globals.shapeGraph = ConjunctiveGraph()
        globals.namespaces = dict()
        

    #def addUnseenVariablesToGraph(self, triples):
    #    for triple in triples:
    #        self.addTripleToShapeGraph((triple.subject,triple.predicat, triple.object))
    #        print("Triple ADDED: " + str((triple.subject,triple.predicat, triple.object)))