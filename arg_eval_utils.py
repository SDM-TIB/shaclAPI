from travshacl.core.GraphTraversal import GraphTraversal


def parse_traversal_string(traversal_string):
    if traversal_string == "DFS":
        return GraphTraversal.DFS
    elif traversal_string == "BFS":
        return GraphTraversal.BFS
    else:
        return None

def parse_heuristics_string(input):
    heuristics = {}
    if not input:
        return heuristics
    if 'TARGET' in input:
        heuristics['target'] = True
    else:
        heuristics['target'] = False

    if 'IN' in input:
        heuristics['degree'] = 'in'
    elif 'OUT' in input:
        heuristics['degree'] = 'out'
    else:
        heuristics['degree'] = False
        
    if 'SMALL' in input:
        heuristics['properties'] = 'small'
    elif 'BIG' in input:
        heuristics['properties'] = 'big'
    else:
        heuristics['properties'] = False
    return heuristics