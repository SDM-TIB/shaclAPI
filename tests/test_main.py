import requests
import json
from tests import testingUtils
import pytest
import os, sys
from glob import glob
import time
import urllib

TRAV_DIR = 'Trav-SHACL/'
FLASK_ENDPOINT='http://localhost:5000/'
MAX_NUMBER_OF_TRIES=10
TESTS_DIRS = [
    './tests/tc1/test_definitions/',
    './tests/tc2/test_definitions/',
    './tests/tc3/test_definitions/',
    './tests/tc4/test_definitions/'
]

required_prefixes = { 
    "test1": "<http://example.org/testGraph1#>",
    "test2": "<http://example.org/testGraph2#>",
    "test3b": "<http://example.org/testGraph3b#>",
    "test4": "<http://example.org/testGraph4#>" }

RESULT_DIR = 'test_output'
if not os.path.isdir(RESULT_DIR):
    os.mkdir(RESULT_DIR)


def get_all_files():
    all_files = []
    for d in TESTS_DIRS:
        test_files = glob(d + '*.json')
        all_files.extend(test_files)
    return all_files

@pytest.mark.dependency()
def test_api_up():
    result = requests.get(FLASK_ENDPOINT)
    assert result.ok == True

@pytest.mark.parametrize("file", get_all_files())
def test_trav(file):
    namespace = testingUtils.get_trav_args(file)
    test_dir = os.getcwd()
    os.chdir(TRAV_DIR)
    try_number = 0
    while MAX_NUMBER_OF_TRIES > try_number:    
        try:
            sys.path.append(os.getcwd())
            from travshacl.TravSHACL import eval_shape_schema
            sys.path.remove(os.getcwd())
            response = eval_shape_schema(namespace)
        except Exception as e:
            if MAX_NUMBER_OF_TRIES > try_number and isinstance(e,(ConnectionResetError,urllib.error.URLError)) :
                print("An Error {} occured retry in 3s... ({}/{})".format(type(e),try_number + 1,MAX_NUMBER_OF_TRIES))
                try_number = try_number + 1
                time.sleep(3)
                continue
            else:
                os.chdir(test_dir)
                raise Exception(e)
        else:
            os.chdir(test_dir)
            break

@pytest.mark.parametrize("file", get_all_files())
@pytest.mark.parametrize("config_file", ['tests/configs/lubm_config.json'])
def test_singleprocessing(file, config_file):
    params, solution, log_file_path = test_setup_from_file(file, config_file, 'single')
    test_api('single', params, solution, log_file_path)

@pytest.mark.parametrize("file", get_all_files())
@pytest.mark.parametrize("config_file", ['tests/configs/lubm_config.json', 'tests/configs/lubm_config_s2spy.json'])
def test_multiprocessing(file, config_file):
    params, solution, log_file_path = test_setup_from_file(file, config_file, 'multi')
    test_api('multi', params, solution, log_file_path)

@pytest.mark.parametrize("file", get_all_files())
@pytest.mark.parametrize("backend", ["travshacl"])
@pytest.mark.parametrize("prune_shape_network", [True, False])
@pytest.mark.parametrize("remove_constraints", [True, False])
@pytest.mark.parametrize("replace_target_query", [True, False])
@pytest.mark.parametrize("start_with_target_shape", [True, False])
@pytest.mark.parametrize("config_file", ['tests/configs/configurationtest_base_config.json'])
def test_configurations_multiprocessing(file, backend, prune_shape_network, 
                                            remove_constraints, replace_target_query, 
                                                start_with_target_shape, config_file):

    if backend == "s2spy" and start_with_target_shape == False:
        pytest.skip("Not a valid combination!")

    params, _, _ = test_setup_from_file(file, config_file, 'multi')
    params['backend'] = backend
    params['prune_shape_network'] = prune_shape_network   
    params['remove_constraints'] = remove_constraints
    params['replace_target_query'] = replace_target_query
    params['start_with_target_shape'] = start_with_target_shape                         
    test_api('multi', params, None,'configtest_logfile.log')

# route can be single or multi
@pytest.mark.skip
def test_api(route, params, solution, log_file_path):
    response = requests.post(FLASK_ENDPOINT + route + 'processing', data=params)
    assert response.status_code == 200, "Server-sided error, check server output for details"
    json_response = response.json()
    if solution:
        try:
            for key in ['validTargets','invalidTargets']:
                json_set_of_tuples = sorted([(item[0], item[1]) for item in json_response[key]], key=lambda x: x[0])
                test_set_of_tuples = sorted([(item[0], item[1]) for item in solution[key]], key=lambda x: x[0])

                if len(json_set_of_tuples) != 0 and len(test_set_of_tuples) != 0:
                    json_set_of_targets, json_set_of_shapes = zip(*json_set_of_tuples)
                    test_set_of_targets, test_set_of_shapes = zip(*test_set_of_tuples)
                    assert json_set_of_targets == test_set_of_targets, "Reported instances differ from expected result for: {}".format(key)
                    # if json_set_of_shapes != test_set_of_shapes:
                    #     differing_shapes = [t for i, t in enumerate(test_set_of_tuples) if t[1] != json_set_of_tuples[i][1]]
                    #     warnings.warn("\nShapes are not equal: {}".format(differing_shapes), UserWarning)
                assert len(json_set_of_tuples) == len(test_set_of_tuples) , "Reported instances differ from expected result for: {}".format(key)
        except Exception as identifier:
            with open(log_file_path,"w") as outputfile:
                outputfile.write(str(identifier))
            raise Exception(str(identifier))
        finally:
            with open(log_file_path,"a") as outputfile:
                outputfile.write(json.dumps(json_response,indent = 4))

@pytest.mark.skip
def test_setup_from_file(file, config, route):
    log_file_name = str(file).replace('/','_')
    log_file_name = log_file_name.replace('.','',1)
    log_file_name = route + log_file_name
    log_file_path = os.path.join(RESULT_DIR,log_file_name)
    if os.path.isfile(log_file_path):
        os.remove(log_file_path)
    test, solution = readTest(file)
    params = test
    params['config'] = config
    if 'test_type' in params:
        del params['test_type']
    params['log_file'] = log_file_path
    return params, solution, log_file_path

@pytest.mark.skip
def readTest(file):
    with open(file,'r') as f:
        result = json.load(f)
    solution = result['result']
    del result['result']
    return (result, solution)