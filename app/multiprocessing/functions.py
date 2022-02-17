from app.reduction import prepare_validation
from app.multiprocessing.Xgjoin.Xgjoin import Xgjoin
from app.multiprocessing.Xgoptional.Xgoptional import Xgoptional
import time, logging
from app.multiprocessing.ThreadEx import ThreadEx
from rdflib import Namespace, URIRef
from app.triple import TripleE

logger = logging.getLogger(__name__)


def mp_post_processing(joined_result_queue, output_queue, timestamp_queue, variables, target_shape, target_var, collect_all_results = False):
    """
    When Xgoptional is used the post processing just has to collect all the results in a hashtable.
    Example Input:
        Joined Result Queue: {'instance': 'http://example.org/testGraph3b#nodeA_0', 'validation': ('ShapeA', True, 'unbound'), 'var': 'x', 'id': 0},...
                                {'instance': 'literal', 'validation': None, 'var': 'lit', 'id': 0} <-- without validation result, produced by the xgoptional.
        Output: [{'instance': 'http://example.org/testGraph3b#nodeA_0', 'validation': ('ShapeA', True, 'unbound'), 'var': 'x'}, {'var': 'lit', 'instance': 'literal'}], ...
    """
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

        # Initalize Hashtable Entry if necessary
        if not item_id in table:
            table[item_id] = {'result': [], 'need': variables.copy()}
        
        try:
            if collect_all_results:
                # Collect all results
                table[item_id]['result'].append(item)
            else: 
                # If only the first validation result per assignment is collected, the validation result of the target_var instance should be the one of the target_shape.
                if ('?' + item['var'] != target_var or item['validation'][0] == target_shape):
                    table[item_id]['need'].remove("?" + item['var'])
                    table[item_id]['result'].append(item)
                else:
                    table[item_id]['result'].append(item)

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
    # if config.target_shape == None:
    #     out_queue.put('EOF')
    #     result_transmitter.done()
    #     return

    schema = prepare_validation(config, query, result_transmitter)
    _ = schema.validate(config.start_with_target_shape) # Validate Schema --> validation results will be put into the out_queue during validation
    
def mp_xjoin(left, right, out_queue, config):
    """
    Function to be executed with Runner to join the instances of the left with the right queue.
    """
    join_instance = Xgoptional(['var', 'instance', 'id'], ['instance', 'validation'], config.memory_size)
    join_instance.execute(left, right, out_queue)

def mp_output_completion(input_queue, output_queue, query):
    t_path = Namespace("//travshacl_path#")
    query.namespace_manager.bind('ts', t_path)
    t_path_valid = t_path['satisfiesShape'].n3(query.namespace_manager)
    t_path_invalid = t_path['violatesShape'].n3(query.namespace_manager)
    
    query_triples = query.get_triples(replace_prefixes=False)

    result = input_queue.get()
    while result != 'EOF':
        logger.debug("Result:" + str(result))
        query_result = result['result']
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
        logger.debug("Binding:" + str(binding))
        logger.debug("Filtered Binding:" + str(filtered_bindings))
        triples = [(binding[t[TripleE.SUBJECT]], t[TripleE.PREDICATE], binding.get(t[TripleE.OBJECT]) or t[TripleE.OBJECT])
                       for t in query_triples if t[TripleE.SUBJECT] in binding]
        logger.debug("Triples:" + str(triples))
        report_triples = [(URIRef(b['instance']).n3(query.namespace_manager), (t_path_valid if b['validation'][1] else t_path_invalid), b['validation'][0])
                           for b in query_result if 'validation' in b and b['validation']]
        logger.debug("Report Triples:" + str(report_triples))
        output_queue.put((filtered_bindings, triples, report_triples))
        result = input_queue.get()