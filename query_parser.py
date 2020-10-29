import argparse
from rdflib.plugins import sparql

import json, glob, re
import sys
sys.path.append('./travshacl')
from travshacl.validation.ShapeParser import ShapeParser
from travshacl.validation.core.GraphTraversal import GraphTraversal
sys.path.remove('./travshacl')

def parse_query(query):
	query_rep = {
		'targetClass': None,
		'constraints': {},
	}
	#Starting with { select everything until last . and ending with }
	where = re.findall(r"\{([^[]*.)[^[]*\}", query)[0]
	#Select everything from \n or \t until . and split it on ' '
	triples = re.findall(r"([^ \t\n]+) ([^ ]+) ([^.\n\}]+)", where)
	query_rep['constraints'] = {p: (s,o) for s,p,o in triples}
	if query_rep['constraints'].get('a'):
		query_rep['targetClass'] = query_rep['constraints']['a'][1]
	return query_rep

def computeEdges(shapes, targetShape):
    """Computes the edges in the network. 
    Based on travshacl.ShapeNetwork.computeEdges"""
    dependencies = {s.getId(): [] for s in shapes}
    reverse_dependencies = {s.getId(): [] for s in shapes}
    for s in shapes:
        refs = s.getShapeRefs()
        if refs:
            name = s.getId()
            dependencies[name] = refs
            #TODO: Track reverse_dependencies only, if they reference the targetShape and appear in the query
            if targetShape in refs:
            	reverse_dependencies[targetShape].append(name)
    return dependencies, reverse_dependencies

def reduce_shape_network(shape_dir, query, graphTraversal):
	shapes = ShapeParser().parseShapesFromDir(args.d, 'JSON', False, 256, False)
	#Identify target shape (shape[i] = targetShape)
	for i, s in enumerate(shapes):
		if s.targetDef == query['targetClass']:
			targetIndex = i
			break
	#Remove constraints not considered
	for c in shapes[i].getConstraints().copy():
		if c.path not in query['constraints']:
			shapes[i].constraints.remove(c)
			if c.getShapeRef():
				shapes[i].referencedShapes.pop(c.getShapeRef())
	#Remove shapes not considered
	involvedShapes = GraphTraversal(graphTraversal).traverse_graph(*computeEdges(shapes, shapes[i].getId()), shapes[i].getId())
	return [s for s in shapes if s.id in involvedShapes]

parser = argparse.ArgumentParser(description='SHACL Constraint Validation over a SPARQL Endpoint')
parser.add_argument('-d', metavar='schemaDir', type=str, default=None,
                        help='Directory containing shapes')
parser.add_argument(dest='graphTraversal', type=str, default='DFS', choices=['BFS', 'DFS'],
                        help='The algorithm used for graph traversal (BFS / DFS)')
parser.add_argument('query', metavar='query', type=str, default=None,
                        help='Name of the directory where results of validation will be saved')
args = parser.parse_args()
query = parse_query(args.query)
if args.graphTraversal == 'DFS':
	graphTraversal = GraphTraversal.DFS
else:
	graphTraversal = GraphTraversal.BFS
print([s.id for s in reduce_shape_network(args.d, query, graphTraversal)])