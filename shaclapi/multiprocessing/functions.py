import logging
import time
from enum import IntEnum
from functools import reduce

from rdflib import Namespace, URIRef

from shaclapi.multiprocessing.Xgoptional.Xgoptional import Xgoptional
from shaclapi.reduction import prepare_validation
from shaclapi.triple import TripleE


class ValReport(IntEnum):
    SHAPE = 0
    IS_VALID = 1
    REASON = 2


logger = logging.getLogger(__name__)


def mp_post_processing(joined_result_queue, output_queue, timestamp_queue, variables, target_shape, target_var, collect_all_results = False):
    """
    The post-processing collects all the bindings belonging to a SPARQL result mapping.

    Example:
        Joined Result Queue (input):
            {'instance': 'http://example.org/testGraph3b#nodeA_0', 'validation': ('ShapeA', True, 'unbound'), 'var': 'x', 'id': 0},...
            {'instance': 'literal', 'validation': None, 'var': 'lit', 'id': 0} <-- without validation result, produced by the xgoptional.

        Output:
            [{'instance': 'http://example.org/testGraph3b#nodeA_0', 'validation': ('ShapeA', True, 'unbound'), 'var': 'x'}, {'var': 'lit', 'instance': 'literal'}], ...
    """
    if 'UNDEF' in target_shape and not collect_all_results:
        collect_all_results = True
        logger.warning('Running in blocking mode as the target variable could not be identified!')

    table = {}
    finished_set = set()
    item = joined_result_queue.get()
    while item != 'EOF':
        item_id = item['id']
        del item['id']

        if item_id in finished_set:
            logger.debug("Received a mapping from an already finished result {}".format(item))
            item = joined_result_queue.get()
            continue

        # Initialize Hashtable Entry if necessary
        if item_id not in table:
            table[item_id] = {'result': [], 'need': variables.copy()}  # TODO: Deal with multiple targets for one variable
        
        try:
            if collect_all_results:
                # Collect all results
                table[item_id]['result'].append(item)
            else: 
                # If only the required validation result per assignment are collected, the validation result can be 
                #  - None (produced by XGoptional)
                #  - a binding not occuring in the target_shape mapping 
                #  - a binding with a validation result matching the target_shape
                binding_var = '?' + item['var']
                if item['validation'] is None or (binding_var not in target_shape.keys() or item['validation'][0] in target_shape[binding_var]):
                    table[item_id]['need'].remove("?" + item['var'])
                    table[item_id]['result'].append(item)
                    logger.debug(f"New Mapping matching target shape: {item}")
                else:
                    table[item_id]['result'].append(item)
                    logger.debug(f"New Mapping not matching target shape: {item}")
        except ValueError:
            logger.debug("Received a duplicate mapping from xgoptional {} --> {}".format(item, table[item_id]))
            item = joined_result_queue.get()
            continue

        # If the Hashtable Entry is complete put it into the output queue; remove it from the Hashtable and add the id to the finished list
        if len(table[item_id]['need']) == 0 and not collect_all_results:
            final_result_item = table[item_id]
            del table[item_id]
            finished_set.add(item_id)
            output_queue.put({'result': final_result_item['result']})
            timestamp_queue.put({'timestamp': time.time()})
            logger.debug('Finished Result {}'.format(final_result_item['result']))

        item = joined_result_queue.get()
    
    if collect_all_results:
        for mapping in table.values():
            output_queue.put({'result': mapping['result']})
            timestamp_queue.put({'timestamp': time.time()})
            logger.debug('Finished Result {}'.format(mapping['result']))


def mp_validate(out_queue, config, query, result_transmitter):
    """
    Function to be executed with Runner to run the validation process of the backend.
    """
    schema = prepare_validation(config, query, result_transmitter)
    _ = schema.validate(config.start_with_target_shape)  # Validate Schema --> validation results will be put into the out_queue during validation


def mp_xjoin(left, right, out_queue, config):
    """
    Function to be executed with Runner to join the instances of the left with the right queue.
    """
    join_instance = Xgoptional(['var', 'instance', 'id'], ['instance', 'validation'], config.memory_size)
    join_instance.execute(left, right, out_queue)


def mp_output_completion(input_queue, output_queue, query, target_shape, is_test_output=False):
    target_shape_list = reduce(lambda a, b: a + b, target_shape.values())
    t_path = Namespace("//travshacl_path#")
    query.namespace_manager.bind('ts', t_path)
    t_path_valid = t_path['satisfiesShape'].n3(query.namespace_manager)
    t_path_invalid = t_path['violatesShape'].n3(query.namespace_manager)
    
    query_triples = query.get_triples(replace_prefixes=False)

    test_output = {"validTargets": set(), "invalidTargets": set(), "advancedValid": set(), "advancedInvalid": set()}
        
    result = input_queue.get()
    while result != 'EOF':
        logger.debug("Result:" + str(result))
        query_result = result['result']
        
        if not is_test_output:
            # Create Bindings
            binding = {}
            filtered_bindings = {}
            for b in query_result:
                try:
                    instance = URIRef(b['instance']).n3(query.namespace_manager)
                except:
                    instance = b['instance']
                binding['?' + b['var']] = instance
                if '?' + b['var'] in query.PV:
                    filtered_bindings['?' + b['var']] = instance
            triples = [
                (binding[t[TripleE.SUBJECT]], t[TripleE.PREDICATE], binding.get(t[TripleE.OBJECT]) or t[TripleE.OBJECT])
                for t in query_triples if t[TripleE.SUBJECT] in binding
            ]
            report_triples = [
                (
                    URIRef(b['instance']).n3(query.namespace_manager),
                    (t_path_valid if b['validation'][1] else t_path_invalid),
                    b['validation'][0]
                )
                for b in query_result if 'validation' in b and b['validation']
            ]
            logger.debug("Report Triples:" + str(report_triples))
            output_queue.put((filtered_bindings, triples, report_triples))
        else:
            for binding in query_result:
                if 'validation' in binding:
                    if binding['validation']:
                        if binding['validation'][ValReport.SHAPE] in target_shape_list:
                            if binding['validation'][ValReport.IS_VALID]:
                                test_output['validTargets'].add((binding['instance'], binding['validation'][ValReport.REASON]))
                            else:
                                test_output['invalidTargets'].add((binding['instance'], binding['validation'][ValReport.REASON]))
                        else:
                            if binding['validation'][ValReport.IS_VALID]:
                                test_output['advancedValid'].add((binding['instance'], binding['validation'][ValReport.REASON]))
                            else:
                                test_output['advancedInvalid'].add((binding['instance'], binding['validation'][ValReport.REASON]))
        result = input_queue.get()

    if is_test_output:
        test_output['validTargets'] = list(test_output['validTargets'])
        test_output['invalidTargets'] = list(test_output['invalidTargets'])
        test_output['advancedValid'] = list(test_output['advancedValid'])
        test_output['advancedInvalid'] = list(test_output['advancedInvalid'])
        output_queue.put(test_output)
