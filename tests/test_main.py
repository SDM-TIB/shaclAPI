import requests
import config_parser as Configs
import json
from tests import testingUtils
import pytest
import os
import itertools

FLASK_ENDPOINT='http://localhost:5000/'
TESTS_DIRS = [
    './tests/tc1/test_definitions',
    './tests/tc2/test_definitions',
    './tests/tc3/test_definitions',
    './tests/tc4/test_definitions'
]

def test_api_up():
    result = requests.get(FLASK_ENDPOINT)
    assert result.ok == True

#def test_external_endpoint_up():
#    config = Configs.read_and_check_config(PARAMS['config'])
#    result = requests.get(config['external_endpoint'])
#    assert result.ok == True

#files creates the cross-join of all dir-file-combinations.
#Which are reduced afterwards. Not efficient, but easy...
files = [os.path.join(*x) for x in itertools.product(TESTS_DIRS, ['test1.json', 'test2.json', 'test3.json', 'test4.json'])]
files = [f for f in files if os.path.exists(f)]
@pytest.mark.parametrize("file", files)
def test_run(file):
    if not os.path.exists(file):
        return
    test = testingUtils.executeTest(file)
    PARAMS = test[0]
    test_type = test[0]['test_type']
    del PARAMS['test_type']
    response = requests.post(FLASK_ENDPOINT + 'go', data=PARAMS)
    json_response = response.json()
    if test_type == testingUtils.TestType.ONLY_VALID:
        del json_response['invalidTargets']
    elif test_type == testingUtils.TestType.ONLY_INVALID:
        del json_response['validTargets']
    assert set(json_response) == set(test[1])
    #testingUtils.writeTest('tests/test_definitions/lubm1.json', response.json(), query,testingUtils.TestType.ONLY_VALID)

#def test_createTest():
#    testingUtils.testFromExecution(file='tests/test_definitions/test4.json',
#                                    query_file='query.sparql',
#                                    test_type= testingUtils.TestType.BOTH,
#                                    config= 'tests/configs/lubm_config.json', 
#                                    schemaDir='./tests/setup/shapes/smallFamily',
#                                    targetShape='Person')