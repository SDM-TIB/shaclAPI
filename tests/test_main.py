import requests
import config_parser as Configs
import json
from tests import testingUtils
import pytest
import os

FLASK_ENDPOINT='http://localhost:5000/go'
TESTS_DIR = 'tests/test_definitions'


#def test_external_endpoint_up():
#    config = Configs.read_and_check_config(PARAMS['config'])
#    result = requests.get(config['external_endpoint'])
#    assert result.ok == True

@pytest.mark.parametrize("file", ['lubm1.json','lubm2.json'])
def test_run(file):
    test = testingUtils.executeTest(os.path.join(TESTS_DIR, file))
    PARAMS = test[0]
    test_type = test[0]['test_type']
    del PARAMS['test_type']
    response = requests.post(FLASK_ENDPOINT, data=PARAMS)
    json_response = response.json()
    if test_type == testingUtils.TestType.ONLY_VALID:
        del json_response['invalidTargets']
    elif test_type == testingUtils.TestType.ONLY_INVALID:
        del json_response['validTargets']
    assert json_response == test[1]
    #testingUtils.writeTest('tests/test_definitions/lubm1.json', response.json(), query,testingUtils.TestType.ONLY_VALID)



