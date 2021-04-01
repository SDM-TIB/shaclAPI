from rdflib import Namespace, URIRef
from enum import IntEnum

class ValReport(IntEnum):
    SHAPE = 0
    IS_VALID = 1
    REASON = 2

#TODO: Create Output which uses XJoin

class BaseResult:
    '''
    The BaseResult includes all information which is needed to construct an output. 
    Each URIRef is non abbreviated!

    validation_report_triples: {instance: (shape of instance, is_valid, violating/validating shape)}
    query_results: {'query_var': 'prefix:instance'}
    '''
    def __init__(self, validation_report_triples, query_results, query):
        self.validation_report_triples = validation_report_triples
        self.query_results = query_results
        self.query = query

    @staticmethod
    def from_travshacl(validation_report, query, query_results):
        conv_val_report = parse_travshacl_report(
            validation_report, query.namespace_manager)
        #This will convert the entries to a notation which uses Prefixes
        conv_query_results = [{k: v['value'] for k, v in entry.items(
                                    )} for entry in query_results['results']['bindings']]
        return BaseResult(conv_val_report, conv_query_results, query)
    
    @staticmethod
    def from_travshaclBase(validation_queue, query, query_queue):
        #This will convert the entries to a notation which uses Prefixes
        actual_tuple = query_queue.get()
        conv_query_results = []
        while actual_tuple != 'EOF':
            conv_query_results += [actual_tuple]
            actual_tuple = query_queue.get()

        conv_val_report = {}
        actual_tuple = validation_queue.get()
        while actual_tuple != 'EOF':
            conv_val_report[actual_tuple[0]] = actual_tuple[1:4]
            actual_tuple = validation_queue.get() 
        print(conv_val_report)
        return BaseResult(conv_val_report, conv_query_results, query)
    
    @staticmethod
    def from_shacl2sparql(validation_report, query, query_results):
        raise NotImplementedError


def parse_travshacl_report(report, namespace_manager):
    reportResults = {}
    for shape, instance_dict in report.items():
        for is_valid, instances in instance_dict.items():
            for instance in instances:
                reportResults[instance[1]] = (instance[0], (is_valid == 'valid_instances'), shape)
    return reportResults
