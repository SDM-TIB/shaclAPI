from TravSHACL.sparql.SPARQLEndpoint import SPARQLEndpoint

from shaclapi.reduction.s2spy.ReducedShapeSchema import ReducedShapeSchema as ReducedShapeSchemaS2Spy
from shaclapi.reduction.travshacl.ReducedShapeSchema import ReducedShapeSchema as ReducedShapeSchemaTravShacl


def prepare_validation(config, query, result_transmitter):
    """
    Given a Config Object (app/config.py), a Query Object (app/query.py) and an Result Transmitter Object, 
    which will be used to for non-blocking transmission of validation results from the backend to the api,
    this methode will prepare a matching ShapeSchema to be used for validation.
    """
    # Prepare the backend and choose the matching inherited ShapeSchema.
    if config.backend == 'travshacl':
        ShapeSchema = ReducedShapeSchemaTravShacl
        SPARQLEndpoint.instance = None  # The SPARQLEndpoint Object of Travshacl is a singleton, so we need to rest it otherwise it won't change
    elif config.backend == 's2spy':
        ShapeSchema = ReducedShapeSchemaS2Spy
    else:
        raise NotImplementedError('The given backend {} is not implemented'.format(config.backend))
    
    # Initialize the ShapeSchema, this will parse the Shapes from the files and reduce the network as configured.
    shape_schema = ShapeSchema.from_config(config, query, result_transmitter)
    return shape_schema
