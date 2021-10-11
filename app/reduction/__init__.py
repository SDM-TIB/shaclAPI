import sys

# Makes travshacl / s2spy packages accesible without adding __init__.py to the backend directories
sys.path.append('./s2spy')
sys.path.append('./Trav-SHACL')  
from app.reduction.travshacl.ReducedShapeSchema import ReducedShapeSchema as ReducedShapeSchemaTravShacl
from app.reduction.s2spy.ReducedShapeSchema import ReducedShapeSchema as ReducedShapeSchemaS2Spy
from travshacl.sparql.SPARQLEndpoint import SPARQLEndpoint
sys.path.remove('./Trav-SHACL')
sys.path.remove('./s2spy')

sys.path.append('./s2spy/validation')
import validation.sparql.SPARQLPrefixHandler as SPARQLPrefixHandler
sys.path.remove('./s2spy/validation')

def prepare_validation(config, query, result_transmitter):
    '''
    Given a Config Object (app/config.py), a Query Object (app/query.py) and an Result Transmitter Object, 
    which will be used to for non-blocking transmission of validation results from the backend to the api,
    this methode will prepare a matching ShapeSchema to be used for validation.
    '''

    # Prepare the backend and choose the matching inherited ShapeSchema.
    if config.backend == "travshacl":
        ReducedShapeSchema = ReducedShapeSchemaTravShacl
        SPARQLEndpoint.instance = None # The SPARQLEndpoint Object of Travshacl is a singleton, so we need to rest it otherwise it won't change
    elif config.backend == "s2spy":
        SPARQLPrefixHandler.prefixes = {str(key): "<" + str(value) + ">" for (key, value) in query.namespace_manager.namespaces()}
        SPARQLPrefixHandler.prefixString = "\n".join(["".join("PREFIX " + key + ":" + value) for (key, value) in SPARQLPrefixHandler.prefixes.items()]) + "\n"
        ReducedShapeSchema = ReducedShapeSchemaS2Spy
    else:
        raise NotImplementedError("The given backend {} is not implemented".format(config.backend))
    
    # Initalize the ShapeSchema, this will parse the Shapes from the files and reduce the network as configured. 
    schema = ReducedShapeSchema.from_config(config, query, result_transmitter)
    return schema