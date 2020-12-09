from rdflib import ConjunctiveGraph, URIRef, Namespace, Literal
from rdflib.namespace import RDF, OWL

NAMESPACE = Namespace("http://example.org/testGraph#") 

graph = ConjunctiveGraph()
graph.bind('test', NAMESPACE)

NO_OF_CLASSES = 4

#nodeA a classA
for i in range(20):
    sub = NAMESPACE['nodeA_{}'.format(i)]
    graph.add((sub, RDF.type, NAMESPACE.classA))
#nodeA refersTo D
for i in range(15):
    sub = NAMESPACE['nodeA_{}'.format(i)]
    pred = NAMESPACE.refersTo
    obj = NAMESPACE['nodeD_0']
    graph.add((sub, pred, obj))
#nodeA hasLiteral
for i in range(10):
    sub = NAMESPACE['nodeA_{}'.format(i)]
    pred = NAMESPACE.hasLiteral
    obj = Literal('valid_value')
    graph.add((sub, pred, obj))
#nodeA refersTo B (valid)
for i in range(5):
    sub = NAMESPACE['nodeA_{}'.format(i)]
    pred = NAMESPACE.refersTo
    obj = NAMESPACE['nodeB_0']
    graph.add((sub, pred, obj))
#nodeA refersTo B (violated)
for i in range(5, 15):
    sub = NAMESPACE['nodeA_{}'.format(i)]
    pred = NAMESPACE.refersTo
    obj = NAMESPACE['nodeB_1']
    graph.add((sub, pred, obj))

#nodeB a classB
for i in range(2):
    sub = NAMESPACE['nodeB_{}'.format(i)]
    graph.add((sub, RDF.type, NAMESPACE.classB))
#nodeB refersTo C
sub = NAMESPACE['nodeB_0']
pred = NAMESPACE.refersTo
obj = NAMESPACE['nodeC_0']
graph.add((sub, pred, obj))

#nodeC a classC
sub = NAMESPACE['nodeC_0']
graph.add((sub, RDF.type, NAMESPACE.classC))
#nodeC refersTo D
sub = NAMESPACE['nodeC_0']
pred = NAMESPACE.refersTo
obj = NAMESPACE['nodeD_0']
graph.add((sub, pred, obj))

#nodeD a classD
sub = NAMESPACE['nodeD_0']
graph.add((sub, RDF.type, NAMESPACE.classD))
#nodeD hasLiteral
sub = NAMESPACE['nodeD_0']
pred = NAMESPACE.hasLiteral
obj = Literal('valid_value')
graph.add((sub, pred, obj))

graph.serialize(destination='tc2_testgraph.owl', format='pretty-xml')