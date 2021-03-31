import json
from argparse import Namespace
import os

from flask.globals import request

from app.query import Query
import sys
sys.path.append('./Trav-SHACL') # Makes travshacl Package accesible without adding __init__.py to travshacl/ Directory
from reduction.ReducedShapeSchema import ReducedShapeSchema, ReturnShapeSchema
from travshacl.TravSHACL import parse_heuristics
import travshacl.sparql.SPARQLPrefixHandler as SPARQLPrefixHandler
from travshacl.core.GraphTraversal import GraphTraversal
sys.path.remove('./Trav-SHACL')

import config_parser as Configs
from SPARQLWrapper import SPARQLWrapper, JSON

INTERNAL_SPARQL_ENDPOINT = "http://localhost:5000/endpoint"

def parse_validation_params(request_form):
    traversal_strategie = GraphTraversal[request.form['traversalStrategie']]
    schema_directory = request_form['schemaDir']
    heuristics = parse_heuristics(request_form['heuristic'])
    targetShapeID = request_form['targetShape']
   
    config = Configs.read_and_check_config(request_form.get('config', 'config.json'))

    config['internal_endpoint'] = config['external_endpoint']
    config['external_endpoint'] = INTERNAL_SPARQL_ENDPOINT if config['debugging'] else config['external_endpoint']
    config['traversalStrategie'] = request_form['traversalStrategie']
    config['heuristic'] = request_form['heuristic']

    return traversal_strategie, schema_directory, heuristics, config, targetShapeID

def prepare_validation(query, traversal_strategie, schema_directory, heuristics, config, targetShapeID=None):
    SPARQLPrefixHandler.prefixes = {str(
        key): "<" + str(value) + ">" for (key, value) in query.namespace_manager.namespaces()}
    SPARQLPrefixHandler.prefixString = "\n".join(["".join(
        "PREFIX " + key + ":" + value) for (key, value) in SPARQLPrefixHandler.prefixes.items()]) + "\n"

    if targetShapeID is None:
        schema = ReturnShapeSchema(
            schema_directory, config['shapeFormat'], config['internal_endpoint'], traversal_strategie,
            heuristics, config['useSelectiveQueries'], config['maxSplit'], config['outputDirectory'],
            config['ORDERBYinQueries'], config['outputs'], config['workInParallel'])
    else:
        schema = ReducedShapeSchema(
            schema_directory, config['shapeFormat'], config['internal_endpoint'], traversal_strategie,
            heuristics, config['useSelectiveQueries'], config['maxSplit'], config['outputDirectory'],
            config['ORDERBYinQueries'], config['outputs'], config['workInParallel'], targetShapeID, query)

    return schema