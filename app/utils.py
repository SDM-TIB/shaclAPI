import sys, os

sys.path.append('./s2spy')
sys.path.append('./Trav-SHACL') # Makes travshacl Package accesible without adding __init__.py to travshacl/ Directory
from app.reduction.travshacl.ReducedShapeSchema import ReducedShapeSchema as ReducedShapeSchemaTravShacl
from app.reduction.s2spy.ReducedShapeSchema import ReducedShapeSchema as ReducedShapeSchemaS2Spy
from travshacl.sparql.SPARQLEndpoint import SPARQLEndpoint
sys.path.remove('./Trav-SHACL')
sys.path.remove('./s2spy')

sys.path.append('./s2spy/validation')
import validation.sparql.SPARQLPrefixHandler as SPARQLPrefixHandler
sys.path.remove('./s2spy/validation')

import app.colors as Colors
from SPARQLWrapper import SPARQLWrapper, JSON

def prepare_validation(config, query, result_transmitter):
    if config.backend == "travshacl":
        ReducedShapeSchema = ReducedShapeSchemaTravShacl
        SPARQLEndpoint.instance = None # Travshacl uses a singleton, the endpoint won't change otherwise
    elif config.backend == "s2spy":
        SPARQLPrefixHandler.prefixes = {str(key): "<" + str(value) + ">" for (key, value) in query.namespace_manager.namespaces()}
        SPARQLPrefixHandler.prefixString = "\n".join(["".join("PREFIX " + key + ":" + value) for (key, value) in SPARQLPrefixHandler.prefixes.items()]) + "\n"
        ReducedShapeSchema = ReducedShapeSchemaS2Spy
    else:
        raise NotImplementedError
    
    schema = ReducedShapeSchema.from_config(config, query, result_transmitter)
    return schema

def dict_to_csv(input, file_descriptor, write_header=False):
    content = ",".join([str(value) for value in input.values()]) + '\n'
    if write_header:
        header = ",".join([str(key) for key in input.keys()]) + '\n'
        file_descriptor.write(header)
    file_descriptor.write(content)

def write_list_of_dicts(input, path_to_csv):
    if not os.path.isfile(path_to_csv):
        with open(path_to_csv, "w") as f:
            dict_to_csv(input[0], f, write_header=True)
            for i in range(1,len(input)):
                dict_to_csv(input[i], f)
    else:
        with open(path_to_csv, "a") as f:
            for i in range(0,len(input)):
                dict_to_csv(input[i], f)
