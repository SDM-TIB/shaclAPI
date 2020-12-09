from rdflib import ConjunctiveGraph, URIRef, Namespace, Literal
from rdflib.namespace import RDF, OWL

NAMESPACE = Namespace("http://example.org/testGraph#") 

graph = ConjunctiveGraph()
graph.bind('test', NAMESPACE)

NO_OF_CLASSES = 3

#nodeA a classA
for i in range(20):
    sub = NAMESPACE['nodeA_{}'.format(i)]
    graph.add((sub, RDF.type, NAMESPACE.classA))
#nodeA nonShapeLiteral
for i in range(5):
    sub = NAMESPACE['nodeA_{}'.format(i)]
    obj = NAMESPACE.nonShapeLiteral
    graph.add((sub, obj, Literal('nonshape_value')))
sub = NAMESPACE['nodeA_10']
obj = NAMESPACE.nonShapeLiteral
graph.add((sub, obj, Literal('nonshape_value')))
sub = NAMESPACE['nodeA_11']
obj = NAMESPACE.nonShapeLiteral
graph.add((sub, obj, Literal('nonshape_value')))

#nodeB a classB
for i in range(3):
    sub = NAMESPACE['nodeB_{}'.format(i)]
    graph.add((sub, RDF.type, NAMESPACE.classB))
#nodeB refersTo A
sub = NAMESPACE['nodeB_0']
pred = NAMESPACE.refersTo
for i in range(10):
    obj = NAMESPACE['nodeA_{}'.format(i)]
    graph.add((sub, pred, obj))
sub = NAMESPACE['nodeB_1']
pred = NAMESPACE.refersTo
for i in range(15):
    obj = NAMESPACE['nodeA_{}'.format(i)]
    graph.add((sub, pred, obj))
sub = NAMESPACE['nodeB_2']
pred = NAMESPACE.refersTo
for i in range(10,15):
    obj = NAMESPACE['nodeA_{}'.format(i)]
    graph.add((sub, pred, obj))
#nodeB refersTo C
sub = NAMESPACE['nodeB_0']
pred = NAMESPACE.refersTo
obj = NAMESPACE['nodeC_0']
sub = NAMESPACE['nodeB_1']
pred = NAMESPACE.refersTo
obj = NAMESPACE['nodeC_0']

#nodeC a classC
sub = NAMESPACE['nodeC_0']
graph.add((sub, RDF.type, NAMESPACE.classC))

graph.serialize(destination='tc4_testgraph.owl', format='pretty-xml')