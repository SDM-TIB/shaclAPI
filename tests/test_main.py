import requests
import config_parser as Configs
import json
from tests import testingUtils
import pytest
import os

FLASK_ENDPOINT='http://localhost:5000/'
#TESTS_DIR = 'tests/test_definitions'
#TESTS_DIR = 'tests/tc2/test_definitions'
TESTS_DIR = 'tests/tc4/test_definitions'

def test_api_up():
    result = requests.get(FLASK_ENDPOINT)
    assert result.ok == True

#def test_external_endpoint_up():
#    config = Configs.read_and_check_config(PARAMS['config'])
#    result = requests.get(config['external_endpoint'])
#    assert result.ok == True

#@pytest.mark.parametrize("file", ['test1.json', 'test2.json', 'test3.json', 'test4.json'])
@pytest.mark.parametrize("file", ['test1.json', 'test2.json', 'test3.json'])
#@pytest.mark.parametrize("file", ['dbpedia1.json', 'test1.json', 'test3.json'])
def test_run(file):
    test = testingUtils.executeTest(os.path.join(TESTS_DIR, file))
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