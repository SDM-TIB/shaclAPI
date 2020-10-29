import argparse
from rdflib.plugins import sparql

import json, glob, re
import sys
sys.path.append('./travshacl')
from travshacl.validation.ShapeParser import ShapeParser
sys.path.remove('./travshacl')

initNs={"rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#", "dbo":"http://dbpedia.org/ontology/"}

def parse_query(query):
	query_rep = {
		'targetClass': None,
		'constraints': {},
	}
	where = re.findall(r"\{([^[]*.)[^[]*\}", query)[0]
	triples = re.findall(r"(\?[^.]*)", where)
	for t in triples:
		s, p, o = t.split(' ')
		query_rep['constraints'][p] = (s, o)
	if query_rep['constraints'].get('a'):
		query_rep['targetClass'] = query_rep['constraints']['a'][1]
	return query_rep

def reduce_shape_network(shape_dir, query):
	shapes = ShapeParser().parseShapesFromDir(args.d, 'JSON', False, 256, False)
	shape_dict = {s.id: s for s in shapes}
	targetShape = None
	for s in shapes:
		if s.targetDef == query['targetClass']:
			targetShape = s
	targetConstraints = targetShape.getConstraints()
	print([c.path for c in targetShape.getConstraints()])
	print(targetShape.referencedShapes)
	for c in targetConstraints:
		if c.path not in query['constraints'].keys():
			targetConstraints.remove(c)
			if c.getShapeRef():
				targetShape.referencedShapes.pop(c.getShapeRef())
	s.constraints = targetConstraints
	print([c.path for c in targetShape.getConstraints()])
	print(targetShape.referencedShapes)


parser = argparse.ArgumentParser(description='SHACL Constraint Validation over a SPARQL Endpoint')
parser.add_argument('-d', metavar='schemaDir', type=str, default=None,
                        help='Directory containing shapes')
parser.add_argument('query', metavar='query', type=str, default=None,
                        help='Name of the directory where results of validation will be saved')
args = parser.parse_args()
query = parse_query(args.query)
print(query)
reduce_shape_network(args.d, query)