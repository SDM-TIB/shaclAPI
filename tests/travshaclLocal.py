import json
import os
from argparse import Namespace

EXTERNAL_ENDPOINT_LOCALHOST = 'http://0.0.0.0:9000/sparql'

DEFAULT_PARAMS = {
    "task": "a",
    "traversalStrategie": "DFS",
    "schemaDir": "shapes/lubm",
    "heuristic": "TARGET IN BIG",
    "query": "QUERY",
    "targetShape": "FullProfessor",
    "config": "tests/configs/lubm_config.json"
}


def get_trav_args(params_file):
    with open(params_file, 'r') as f:
        params = json.load(f)
    with open(params['config'], 'r') as c:
        json_config = json.load(c)
    with open(DEFAULT_PARAMS['config'], 'r') as c:
        def_config = json.load(c)

    task = params['task'] or DEFAULT_PARAMS['task']
    args = {
        'd': os.path.realpath(params.get('schemaDir') or DEFAULT_PARAMS['schemaDir']),
        'endpoint': EXTERNAL_ENDPOINT_LOCALHOST,
        'graphTraversal': params.get('traversalStrategie') or DEFAULT_PARAMS['traversalStrategie'],
        'heuristics': params.get('heuristic') or DEFAULT_PARAMS['heuristic'],
        'm': json_config.get('maxSplit') or def_config['maxSplit'],
        'orderby': json_config.get('ORDERBYinQueries') or def_config['ORDERBYinQueries'],
        'outputDir': json_config.get('outputDirectory') or def_config['outputDirectory'],
        's2s': json_config.get('SHACL2SPARQLorder') or def_config['SHACL2SPARQLorder'],
        'selective': json_config.get('useSelectiveQueries') or def_config['useSelectiveQueries'],
        'outputs': json_config.get('outputs') or def_config['outputs'],
        'a': 'a' == task,
        'g': 'g' == task,
        's': 's' == task,
        't': 't' == task,
        'f': 'f' == task,
        'json': True
    }
    return Namespace(**args)
