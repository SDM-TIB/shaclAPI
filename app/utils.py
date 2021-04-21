import sys

sys.path.append('./s2spy')
sys.path.append('./Trav-SHACL') # Makes travshacl Package accesible without adding __init__.py to travshacl/ Directory
from app.reduction.travshacl.ReducedShapeSchema import ReducedShapeSchema as ReducedShapeSchemaTravShacl
from app.reduction.s2spy.ReducedShapeSchema import ReducedShapeSchema as ReducedShapeSchemaS2Spy
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
    elif config.backend == "s2spy":
        SPARQLPrefixHandler.prefixes = {str(key): "<" + str(value) + ">" for (key, value) in query.namespace_manager.namespaces()}
        SPARQLPrefixHandler.prefixString = "\n".join(["".join("PREFIX " + key + ":" + value) for (key, value) in SPARQLPrefixHandler.prefixes.items()]) + "\n"
        ReducedShapeSchema = ReducedShapeSchemaS2Spy
    else:
        raise NotImplementedError
    
    schema = ReducedShapeSchema.from_config(config, query, result_transmitter)
    return schema