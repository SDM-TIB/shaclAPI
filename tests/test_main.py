import json
import os
from argparse import Namespace
from glob import glob
from pathlib import Path

import pytest
import requests

FLASK_ENDPOINT = 'http://0.0.0.0:9999/'
EXTERNAL_ENDPOINT_DOCKER = 'http://shaclapi_testdata:8890/sparql'
EXTERNAL_ENDPOINT_LOCALHOST = 'http://0.0.0.0:9000/sparql'
RESULT_DIR = 'output/test_results'

TESTS_DIRS = [
    './tests/tc1/test_definitions/',
    './tests/tc2/test_definitions/',
    './tests/tc3/test_definitions/',
    './tests/tc4/test_definitions/',
    './tests/tc5/test_definitions/',
    './tests/tc_further_border_cases/test_definitions/'
]

required_prefixes = { 
    'test1': '<http://example.org/testGraph1#>',
    'test2': '<http://example.org/testGraph2#>',
    'test3': '<http://example.org/testGraph3#>',
    'test4': '<http://example.org/testGraph4#>',
    'test5': '<http://example.org/testGraph5#>'
}

DEFAULT_PARAMS = {
    'task': 'a',
    'traversalStrategie': 'DFS',
    'schemaDir': 'shapes/lubm',
    'heuristic': 'TARGET IN BIG',
    'query': 'QUERY',
    'targetShape': 'FullProfessor',
    'config': 'tests/configs/lubm_config.json'
}

Path(RESULT_DIR).mkdir(parents=True, exist_ok=True)


def get_all_files():
    all_files = []
    for d in TESTS_DIRS:
        test_files = glob(d + '*.json')
        all_files.extend(test_files)
    return all_files


def test_api_up():
    result = requests.get(FLASK_ENDPOINT)
    assert result.ok


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


@pytest.mark.parametrize('file', get_all_files())
def test_trav(file):
    namespace = get_trav_args(file)
    from TravSHACL.TravSHACL import eval_shape_schema
    try:
        eval_shape_schema(namespace)
    except Exception as e:
        raise Exception(e)


@pytest.mark.parametrize('file', get_all_files())
@pytest.mark.parametrize('config_file', ['tests/configs/lubm_config.json'])
def test_multiprocessing(file, config_file):
    """For each testcase check the correctness of the results the API generates. 

    Parameters
    ----------
    file : str
        The path to the testcase file
    config_file : str
        The path to the configuration of the shaclAPI.
    """
    params, solution, log_file_path = test_setup_from_file(file, config_file, 'multi')
    params['test_identifier'] = file
    params['external_endpoint'] = EXTERNAL_ENDPOINT_DOCKER
    test_api('multi', params, solution, log_file_path)


@pytest.mark.parametrize('file', get_all_files())
@pytest.mark.parametrize('backend', ['travshacl', 's2spy'])
@pytest.mark.parametrize('prune_shape_network', [True, False])
@pytest.mark.parametrize('remove_constraints', [True, False])
@pytest.mark.parametrize('replace_target_query', [True, False])
@pytest.mark.parametrize('start_with_target_shape', [True, False])
@pytest.mark.parametrize('config_file', ['tests/configs/configurationtest_base_config.json'])
@pytest.mark.parametrize('collect_all_validation_results', [True, False])
def test_configurations_multiprocessing(request, file, backend, prune_shape_network, 
                                        remove_constraints, replace_target_query,
                                        start_with_target_shape, collect_all_validation_results, config_file):
    """Test cases checking for exceptions for different setups of the shaclAPI.

    Parameters
    ----------
    file : string   
        The testcase file.
    backend : string
        The SHACL engine to use.
    prune_shape_network : bool
        Whether to prune the shape network.
    remove_constraints : bool
        Whether to remove constraints
    replace_target_query : bool
        Whether to replace the target query.
    start_with_target_shape : bool
        Whether to start with the target shape or leave the decision to the SHACL engine.
    collect_all_validation_results : bool
        Whether to force the collection of at least one validation result per target shape.
    config_file : string
        The basic api configuration file.
    """
    if backend == 's2spy' and not start_with_target_shape:
        pytest.skip('Not a valid combination!')

    if not prune_shape_network and remove_constraints:
        pytest.skip('Not a valid combination!')

    params, _, _ = test_setup_from_file(file, config_file, 'multi')
    params['backend'] = backend
    params['prune_shape_network'] = prune_shape_network   
    params['remove_constraints'] = remove_constraints
    params['replace_target_query'] = replace_target_query
    params['start_with_target_shape'] = start_with_target_shape    
    params['test_identifier'] = 'tests/test_main.py::' + str(request.node.name)
    params['external_endpoint'] = EXTERNAL_ENDPOINT_DOCKER
    params['collect_all_validation_results'] = collect_all_validation_results
    test_api('multi', params, None, 'configtest_logfile.log')
    # Here the metrics can also be tested, but need to disable file output for the metrics
    # test_metrics(params)


# route can be single or multi
@pytest.mark.skip
def test_api(route, params, solution, log_file_path):
    response = requests.post(FLASK_ENDPOINT + route + 'processing', data=params)
    assert response.status_code == 200, 'Server-sided error, check server output for details'
    json_response = response.json()
    print(json_response)
    if solution:
        try:
            for key in ['validTargets', 'invalidTargets']:
                json_set_of_tuples = sorted([(item[0], item[1]) for item in json_response[key]], key=lambda x: x[0])
                test_set_of_tuples = sorted([(item[0], item[1]) for item in solution[key]], key=lambda x: x[0])

                if len(json_set_of_tuples) != 0 and len(test_set_of_tuples) != 0:
                    json_set_of_targets, json_set_of_shapes = zip(*json_set_of_tuples)
                    test_set_of_targets, test_set_of_shapes = zip(*test_set_of_tuples)
                    assert json_set_of_targets == test_set_of_targets, 'Reported instances differ from expected result for: {}'.format(key)
                    # if json_set_of_shapes != test_set_of_shapes:
                    #     differing_shapes = [t for i, t in enumerate(test_set_of_tuples) if t[1] != json_set_of_tuples[i][1]]
                    #     warnings.warn('\nShapes are not equal: {}'.format(differing_shapes), UserWarning)
                assert len(json_set_of_tuples) == len(test_set_of_tuples), 'Reported instances differ from expected result for: {}'.format(key)
        except Exception as identifier:
            with open(log_file_path, 'w') as outputfile:
                outputfile.write(str(identifier))
            raise Exception(str(identifier))
        finally:
            with open(log_file_path, 'a') as outputfile:
                outputfile.write(json.dumps(json_response, indent=4))


@pytest.mark.skip
def test_metrics(params):
    response = requests.post(FLASK_ENDPOINT + 'metrics', data=params)
    assert response.status_code == 200, 'Server-sided error, check server output for details'


@pytest.mark.skip
def test_setup_from_file(file, config, route):
    log_file_name = str(file).replace('/', '_')
    log_file_name = log_file_name.replace('.', '', 1)
    log_file_name = route + log_file_name
    log_file_path = os.path.join(RESULT_DIR, log_file_name)
    if os.path.isfile(log_file_path):
        os.remove(log_file_path)
    test, solution = read_test(file)
    params = test
    params['config'] = config
    if 'test_type' in params:
        del params['test_type']
    params['log_file'] = log_file_path
    return params, solution, log_file_path


@pytest.mark.skip
def read_test(file):
    with open(file, 'r') as f:
        result = json.load(f)
    solution = result['result']
    del result['result']
    return result, solution
