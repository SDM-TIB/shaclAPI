import json
from argparse import Namespace
import os

from flask.globals import request

from app.query import Query
import sys
sys.path.append('./s2spy')
sys.path.append('./Trav-SHACL') # Makes travshacl Package accesible without adding __init__.py to travshacl/ Directory
from app.reduction.travshacl.ReducedShapeSchema import ReducedShapeSchema as ReducedShapeSchemaTravShacl
from app.reduction.s2spy.ReducedShapeSchema import ReducedShapeSchema as ReducedShapeSchemaS2Spy
from travshacl.TravSHACL import parse_heuristics
from travshacl.core.GraphTraversal import GraphTraversal
sys.path.remove('./Trav-SHACL')
sys.path.remove('./s2spy')

sys.path.append('./s2spy/validation')
import validation.sparql.SPARQLPrefixHandler as SPARQLPrefixHandler
sys.path.remove('./s2spy/validation')

import app.colors as Colors
from SPARQLWrapper import SPARQLWrapper, JSON

INTERNAL_SPARQL_ENDPOINT = "http://localhost:5000/endpoint"

CONFIG_DICT = {
    'config.json':['external_endpoint', 'outputDirectory','shapeFormat','workInParallel','useSelectiveQueries','maxSplit','ORDERBYinQueries','SHACL2SPARQLorder','debugging','outputs', 'backend']
}

def parse_validation_params(request_form):
    traversal_strategie = GraphTraversal[request.form['traversalStrategie']]
    schema_directory = request_form['schemaDir']
    heuristics = parse_heuristics(request_form['heuristic'])
    targetShapeID = request_form['targetShape']
   
    config = read_and_check_config(request_form.get('config', 'config.json'))
    
    # The internal_endpoint is that one which is propagated to the backend validation process
    config['internal_endpoint'] = INTERNAL_SPARQL_ENDPOINT if config['debugging'] else config['external_endpoint']
    config['traversalStrategie'] = request_form['traversalStrategie']
    config['heuristic'] = request_form['heuristic']

    return traversal_strategie, schema_directory, heuristics, config, targetShapeID

def prepare_validation(query,replace_target_query, merge_old_target_query, traversal_strategie, schema_directory, heuristics, config, targetShapeID, result_transmitter, backend="travshacl"):
    if backend == "travshacl":
        ReducedShapeSchema = ReducedShapeSchemaTravShacl
    elif backend == "s2spy":
        SPARQLPrefixHandler.prefixes = {str(key): "<" + str(value) + ">" for (key, value) in query.namespace_manager.namespaces()}
        SPARQLPrefixHandler.prefixString = "\n".join(["".join("PREFIX " + key + ":" + value) for (key, value) in SPARQLPrefixHandler.prefixes.items()]) + "\n"
        ReducedShapeSchema = ReducedShapeSchemaS2Spy
    else:
        raise NotImplementedError
    
    schema = ReducedShapeSchema(
            schema_directory, config['shapeFormat'], config['internal_endpoint'], traversal_strategie,
            heuristics, config['useSelectiveQueries'], config['maxSplit'], config['outputDirectory'],
            config['ORDERBYinQueries'], config['outputs'], config['workInParallel'], targetShapeID, query, replace_target_query=replace_target_query, merge_old_target_query=merge_old_target_query, result_transmitter=result_transmitter)
    return schema

def read_and_check_config(file):
    with open(file) as json_config_file:
        config = json.load(json_config_file)
    if file in CONFIG_DICT:
        for item in CONFIG_DICT[file]:
            assert item in config
    return config