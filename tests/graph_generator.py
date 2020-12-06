from glob import glob
import json
from rdflib import Graph, URIRef, Namespace, Literal
from rdflib.namespace import RDF, OWL

SHAPE_PATH = 'shapes/lubm'
AMOUNT = 10

UB = Namespace('http://swat.cse.lehigh.edu/onto/univ-bench.owl#')

'''
shape:
    name - str
    dependencies - {shape: (amount, path)}
    reversed_dependencies - set()
    literals - {path: amount}
'''

def parse_json(dir):
    shapes = {}
    for s in glob(dir+'/*.json'):
        with open(s, 'r') as f:
            shape = json.load(f)

        shape_name = shape['name']
        targetDef = shape['targetDef']['class']
        targetDef = targetDef[targetDef.rfind(':')+1:]


        dependencies = {}
        literals = {}
        for c in shape['constraintDef']['conjunctions'][0]:
            path = c['path']
            path = path[path.rfind(':')+1:]
            amount = c.get('min') or c.get('max')
            if c.get('shape'):
                dependencies[c['shape']] = (path, amount)
            else:
                literals[path] = max(amount, literals.get(path) or 0)

        shapes[shape_name] = {
            'name': shape_name,
            'targetDef': targetDef,
            'dependencies': dependencies,
            'literals' : literals,
        }
    return shapes

def sort_shapes_by_dependencies(shapes):
    reversed_dependencies = {s: set() for s in shapes}
    for shape, values in shapes.items():
        for s in values['dependencies']:
            reversed_dependencies[s].add(shape)
    sorted_shapes = sorted(reversed_dependencies.keys(), key=lambda x: len(reversed_dependencies[x]))
    return sorted_shapes

class GraphGenerator():
    def __init__(self, shape_dict):
        self.graph = Graph()
        self.graph.bind('owl', OWL)
        self.graph.bind('ub', UB)
        o = URIRef('')
        onto = URIRef('http://swat.cse.lehigh.edu/onto/univ-bench.owl')
        self.graph.add((o, RDF.type, OWL.Ontology))
        self.graph.add((o, OWL.imports, onto))
        self.shape_dict = shape_dict
        self.pending_dependencies = {s: [] for s in self.shape_dict.keys()}
        self.shape_counter = {s: 0 for s in self.shape_dict.keys()}

    def __repr__(self):
        return self.graph

    def __str__(self):
        return str(self.shape_counter.items()) + '\n' + str(self.pending_dependencies.items())

    def add_node(self, shape_name):
        node_shape = self.shape_dict[shape_name]
        node_id = self.shape_counter[shape_name]
        self.shape_counter[shape_name] += 1
        node = UB[shape_name+'_{}'.format(node_id)]
        if self.pending_dependencies[shape_name]:
            subject, path = self.pending_dependencies[shape_name].pop(0)
            #print(subject, path, node)
            self.graph.add((subject, UB[path], node))
        self.graph.add((node, RDF.type, UB[node_shape['targetDef']]))
        for path in node_shape['literals']:
            for i in range(node_shape['literals'][path]):
                self.graph.add((node, UB[path], Literal('{}_{}_{}'.format(shape_name.lower(), path.lower(), node_id))))
        for shape, values in node_shape['dependencies'].items():
            path, amount = values
            for i in range(amount):
                self.pending_dependencies[shape] += [(node, path)]

def calc_node_amounts(shapes):
    temp_shapes = shapes.copy()
    sorted_shapes = sort_shapes_by_dependencies(temp_shapes)
    shape_amounts = {s: 0 for s in sorted_shapes}
    shape_amounts[sorted_shapes[0]] = AMOUNT
    while sorted_shapes:
        shape = sorted_shapes.pop(0)
        amount = shape_amounts[shape]
        for s, values in shapes[shape]['dependencies'].items():
            _, factor = values
            shape_amounts[s] += factor*amount
        del(temp_shapes[shape])
        sorted_shapes = sort_shapes_by_dependencies(temp_shapes)
    return shape_amounts

shapes = parse_json(SHAPE_PATH)
shape_amounts = calc_node_amounts(shapes)

g = GraphGenerator(shapes)
for k, v in shape_amounts.items():
    for _ in range(v):
        g.add_node(k)
print(g)
g.graph.serialize(destination='example_graph.owl', format='pretty-xml')