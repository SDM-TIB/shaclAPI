import sys

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


def prepare_validation(config, query, result_transmitter):
    if config.backend == "travshacl":
        ReducedShapeSchema = ReducedShapeSchemaTravShacl
        SPARQLEndpoint.instance = None # Travshacl uses a singleton, the endpoint won't change otherwise
    elif config.backend == "s2spy":
        SPARQLPrefixHandler.prefixes = {str(key): "<" + str(value) + ">" for (key, value) in query.namespace_manager.namespaces()}
        SPARQLPrefixHandler.prefixString = "\n".join(["".join("PREFIX " + key + ":" + value) for (key, value) in SPARQLPrefixHandler.prefixes.items()]) + "\n"
        ReducedShapeSchema = ReducedShapeSchemaS2Spy
    else:
        raise NotImplementedError("The given backend {} is not implemented".format(config.backend))
    
    schema = ReducedShapeSchema.from_config(config, query, result_transmitter)
    return schema

def lookForException(stats_queue):
    exceptions = []
    while not stats_queue.empty():
        item = stats_queue.get()
        if item['topic'] == 'Exception':
            exceptions.append(item['location'])
    if len(exceptions) > 0:
        raise Exception("An Exception occured in " + ' & '.join(exceptions))
