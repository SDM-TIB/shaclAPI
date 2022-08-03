from rdflib import ConjunctiveGraph, Namespace, Literal
from rdflib.namespace import RDF
import json
from os import path


def combineRDFGraphs(graph_file, new_json):
    g = ConjunctiveGraph()
    try:
        g.parse(graph_file)
    except FileNotFoundError:
        pass
    with open(new_json, 'r') as json_file:
        json_data = json.load(json_file)
    NAMESPACE = Namespace(json_data['namespace'])
    g.bind(json_data['bind'], NAMESPACE)
    for c, specs in json_data['classes'].items():  # for each class
        RAW_NODE = c.replace('class', 'node') + '_{}'
        for i in range(specs['nodeAmount']):
            sub = NAMESPACE[RAW_NODE.format(i)]
            g.add((sub, RDF.type, NAMESPACE[c]))
        for path, pathSpecs in specs.items():
            if path == 'nodeAmount':
                continue
            pred = NAMESPACE[path]
            for o_node, o_ids in pathSpecs.items():
                for o_id, s_ids in o_ids.items():
                    if o_node == o_id:
                        obj = Literal(o_node)
                    else:
                        obj = NAMESPACE[o_node + '_' + str(o_id)]
                    for s_id in s_ids:
                        sub = NAMESPACE[RAW_NODE.format(s_id)]
                        g.add((sub, pred, obj))
    g.serialize(destination=graph_file, format='pretty-xml')


if __name__ == '__main__':
    for tc in ['tc1', 'tc2', 'tc3', 'tc4', 'tc5']:
        partGraph = path.join('tests/', tc, 'data/partGraph.json')
        if path.exists(partGraph):
            combineRDFGraphs('tests/setup/TestData/fullTestGraph.owl', partGraph)
