import json
from enum import Enum
import requests
from argparse import Namespace
import os

FLASK_ENDPOINT='http://localhost:5000/'

DEFAULT_PARAMS={
    "task":"a",
    "traversalStrategie":"DFS",
    "schemaDir": "shapes/lubm",
    "heuristic": "TARGET IN BIG",
    "query": "QUERY",
    "targetShape": "FullProfessor",
    "config": "tests/configs/lubm_config.json"
}

class TestType(str,Enum):
    ONLY_VALID = 'valid'
    ONLY_INVALID = 'invalid'
    BOTH = 'both'

def testFromExecution(file, query_file, test_type, config, **args):
    with open(query_file, 'r') as q:
        query = q.read()
    PARAMS = DEFAULT_PARAMS.copy()
    PARAMS.update({"query":query, "config":config})
    PARAMS.update(args)
    print(PARAMS)
    response = requests.post(FLASK_ENDPOINT + 'go', data=PARAMS)
    json_response = response.json()
    writeTest(file,json_response, query, test_type, config=config, **args)


def writeTest(file, response, query,test_type, **args):
    if test_type == TestType.ONLY_VALID:
        del response['invalidTargets']
    elif test_type == TestType.ONLY_INVALID:
        del response['validTargets']
    else:
        pass
    
    given_test_params = {"result": response, "query": query}
    given_test_params.update(args)
    global DEFAULT_PARAMS
    test = DEFAULT_PARAMS.copy()
    test.update(given_test_params)
    with open(file,'w') as f:
        json.dump(test,f, indent=4)

def executeTest(file):
    with open(file,'r') as f:
        result = json.load(f)
    solution = result['result']
    del result['result']
    return (result, solution)
    
def get_trav_args(params_file):
    with open(params_file, 'r') as f:
        params = json.load(f)
    with open(params['config'], 'r') as c:
        json_config = json.load(c)
    with open(DEFAULT_PARAMS['config'], 'r') as c:
        def_config = json.load(c)

    task = params['task'] or DEFAULT_PARAMS['task']
    schemaDir = params.get('schemaDir') \
            or DEFAULT_PARAMS['schemaDir']
    schemaDir = os.path.realpath(schemaDir)
    args = {
        'd': schemaDir,
        'endpoint': json_config.get('external_endpoint') \
            or def_config['external_endpoint'],
        'graphTraversal': params.get('traversalStrategie') \
            or DEFAULT_PARAMS['traversalStrategie'],
        'heuristics': params.get('heuristic') \
            or DEFAULT_PARAMS['heuristic'],
        'm': json_config.get('maxSplit') \
            or def_config['maxSplit'],
        'orderby': json_config.get('ORDERBYinQueries') \
            or def_config['ORDERBYinQueries'],
        'outputDir': json_config.get('outputDirectory') \
            or def_config['outputDirectory'],
        's2s': json_config.get('SHACL2SPARQLorder') \
            or def_config['SHACL2SPARQLorder'],
        'selective': json_config.get('useSelectiveQueries') \
            or def_config['useSelectiveQueries'],
        'outputs': json_config.get('outputs') \
            or def_config['outputs'],
        'a': 'a' == task,
        'g': 'g' == task,
        's': 's' == task,
        't': 't' == task,
        'f': 'f' == task,
    }
    return Namespace(**args)