import json
from enum import Enum
import requests

FLASK_ENDPOINT='http://localhost:5000/'

DEFAULT_PARAMS={
    "task":"a",
    "traversalStrategie":"DFS",
    "schemaDir": "shapes/lubm",
    "heuristic": "TARGET IN BIG",
    "query": "QUERY",
    "targetShape": "FullProfessor",
    "config": "tests/config.json"
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
    writeTest(file,json_response, query, test_type, config=config)


def writeTest(file, response, query,test_type, **args):
    if test_type == TestType.ONLY_VALID:
        del response['invalidTargets']
    elif test_type == TestType.ONLY_INVALID:
        del response['validTargets']
    else:
        pass
    
    given_test_params = {"result": response, "query": query, "test_type": test_type}
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
    
    