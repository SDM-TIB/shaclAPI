import requests
import config_parser as Configs
import json
from tests import testingUtils
import pytest, warnings
import os
import itertools
from glob import glob

FLASK_ENDPOINT='http://localhost:5000/'
TESTS_DIRS = [
    './tests/tc1/test_definitions/',
    './tests/tc2/test_definitions/',
    './tests/tc3/test_definitions/',
    './tests/tc4/test_definitions/'
]

def get_all_files():
    all_files = []
    for d in TESTS_DIRS:
        test_files = glob(d+'*.json')
        all_files.extend(test_files)
    return all_files

@pytest.mark.dependency()
def test_api_up():
    result = requests.get(FLASK_ENDPOINT)
    assert result.ok == True

#def test_external_endpoint_up():
#    config = Configs.read_and_check_config(PARAMS['config'])
#    result = requests.get(config['external_endpoint'])
#    assert result.ok == True


@pytest.mark.parametrize("file", get_all_files())
@pytest.mark.dependency(depends=["test_api_up"])
def test_run(file):
    test = testingUtils.executeTest(file)
    PARAMS = test[0]
    if 'test_type' in PARAMS:
        del PARAMS['test_type']
    response = requests.post(FLASK_ENDPOINT + 'go', data=PARAMS)
    assert response.status_code == 200, "Server-sided error, check server output for details"
    json_response = response.json()
    for key in test[1].keys():
        json_set_of_tuples = sorted([(item[0], item[1]) for item in json_response[key]], key=lambda x: x[0])
        test_set_of_tuples = sorted([(item[0], item[1]) for item in test[1][key]], key=lambda x: x[0])

        if len(json_set_of_tuples) != 0 and len(test_set_of_tuples) != 0:
            json_set_of_targets, json_set_of_shapes = zip(*json_set_of_tuples)
            test_set_of_targets, test_set_of_shapes = zip(*test_set_of_tuples)
            assert json_set_of_targets == test_set_of_targets, "Reported instances differ from expected result for: {}".format(key)
            if json_set_of_shapes != test_set_of_shapes:
                differing_shapes = [t for i, t in enumerate(test_set_of_tuples) if t[1] != json_set_of_tuples[i][1]]
                warnings.warn("\nShapes are not equal: {}".format(differing_shapes), UserWarning)
        assert len(json_set_of_tuples) == len(test_set_of_tuples)  
   
   
    #testingUtils.writeTest('tests/test_definitions/lubm1.json', response.json(), query,testingUtils.TestType.ONLY_VALID)

#def test_createTest():
#    testingUtils.testFromExecution(file='tests/test_definitions/test4.json',
#                                    query_file='query.sparql',
#                                    test_type= testingUtils.TestType.BOTH,
#                                    config= 'tests/configs/lubm_config.json', 
#                                    schemaDir='./tests/setup/shapes/smallFamily',
#                                    targetShape='Person')