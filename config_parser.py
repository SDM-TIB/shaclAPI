import json

CONFIG_DICT = {
    'config.json':['outputDirectory','shapeFormat','workInParallel','useSelectiveQueries','maxSplit','ORDERBYinQueries','SHACL2SPARQLorder','external_endpoint']
}

def read_and_check_config(file):
    with open(file) as json_config_file:
        config = json.load(json_config_file)
    if file in CONFIG_DICT:
        for item in CONFIG_DICT[file]:
            assert item in config
    return config