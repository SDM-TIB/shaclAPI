from app.utils import prepare_validation
from app.multiprocessing.Xjoin.Xjoin import XJoin
from app.multiprocessing.Xgjoin.Xgjoin import Xgjoin
import time, logging
from app.multiprocessing.ThreadEx import ThreadEx

logger = logging.getLogger(__name__)


def mp_post_processing(shape_variables_queue, joined_result_queue, query_result_queue, final_result_queue, timestamp_queue, queue_timeout):
    """
    Transforms the joined output and the raw query result to the final output.
    Example:
    Input: 
        Query Queue: {'query_result': {'x': 'http://example.org/testGraph3b#nodeA_0', 'lit': 'literal' } , 'id': 0}, ...
        Joined Result Queue: {'instance': 'http://example.org/testGraph3b#nodeA_0', 'validation': ('ShapeA', True, 'unbound'), 'var': 'x', 'id': 0},...
    Output: [{'instance': 'http://example.org/testGraph3b#nodeA_0', 'validation': ('ShapeA', True, 'unbound'), 'var': 'x'}, {'var': 'lit', 'instance': 'literal'}], ...
    """
    # First wait for shape variables to be identified
    shape_vars = set()
    new_vars = shape_variables_queue.get()
    while new_vars != 'EOF':
        shape_vars.update(new_vars)
        new_vars = shape_variables_queue.get()
    logger.debug("Shape Variables identified! {}".format(str(shape_vars)))

    # Prepare Hashtable (id --> {result: _, further_query_results: "Query Results which we only need if there are Shapes which don't need to be validated and thus won't occure in the joined results", need: "Set of Variables which will get a Validation Result from the Joined Validation Result queue", 
    #                               got_query_result: "If we already received the binding from the query queue"})
    table = {}
    finished_set = set()

    # Start a Thread for both incoming Queues
    t_query = ThreadEx(target=mp_post_processing_query_thread, args=(table, query_result_queue, final_result_queue, timestamp_queue, shape_vars, finished_set))
    t_joined_results = ThreadEx(target=mp_post_processing_joined_result_thread, args=(table, joined_result_queue, final_result_queue, timestamp_queue, shape_vars, finished_set))
    t_query.start()
    t_joined_results.start()
    t_query.join()
    t_joined_results.join()

    # Adding of results which where skipped in validation (for example because the matching target could be invalidated earlier)
    for id, item in table.items():
        if id not in finished_set:
            logger.debug("item {} ".format(id) + str(item))
            result = item['result']
            missing_validation_results = [item['further_query_results'][var[1:]] for var in item['need']]
            result.extend(missing_validation_results)
            logger.warning("Found unfinished result {}".format(item))
            logger.debug("Instead using: {}".format(result))
            final_result_queue.put({'result': result})

def mp_post_processing_query_thread(table, queue, out_queue, timestamp_queue, shape_vars, finished_set):
    item = queue.get()
    while item != 'EOF':
        item_id = item['id']
        del item['id']

        # Initalize Hashtable Entry if necessary
        if not item_id in table:
            table[item_id] = {'result': [], "further_query_results": {}, 'need': shape_vars.copy(), 'got_query_result': False}

        # Add all query result bindings which will not be validated and therefore won't occure in the joined results.
        logger.debug('Query Result {}'.format(item_id))
        table[item_id]['result'].extend([{'var': var, 'instance': instance, 'validation': None} for var, instance in item['query_result'].items() if not "?" + var in shape_vars])
        table[item_id]['further_query_results'].update({var: {'var': var, 'instance': instance, 'validation': None} for var, instance in item['query_result'].items() if "?" + var in shape_vars})
        table[item_id]['got_query_result'] = True

        # If the Hashtable Entry is complete put it into the output queue; remove it from the Hashtable and add the id to the finished list
        if len(table[item_id]['need']) == 0 and table[item_id]['got_query_result'] == True:
            try:
                finished_set.add(item_id)
                final_result_item = table[item_id]
                del table[item_id]
            except KeyError:
                pass # Only the thread which deletes the item from the table is allowed to write it into the output
            else:
                out_queue.put({'result': final_result_item['result']})
                timestamp_queue.put({'timestamp': time.time()})
                logger.debug('Finished Result {}'.format(item_id))
        item = queue.get()
    logger.debug('Query thread is done!')

def mp_post_processing_joined_result_thread(table, queue, out_queue, timestamp_queue, shape_vars, finished_set):
    item = queue.get()
    while item != 'EOF':
        item_id = item['id']
        del item['id']

        # Initalize Hashtable Entry if necessary
        if not item_id in table:
            table[item_id] = {'result': [], "further_query_results": {}, 'need': shape_vars.copy(), 'got_query_result': False}
        
        # Add joined validation with binding to the result
        logger.debug('Validation Result {}-{}'.format(item_id, item['var']))
        table[item_id]['result'].append(item)
        try:
            table[item_id]['need'].remove("?" + item['var'])
        except KeyError:
            logger.warning("Got unneeded validation result! {} --> {}".format(item, table[item_id]))

        # If the Hashtable Entry is complete put it into the output queue; remove it from the Hashtable and add the id to the finished list
        if len(table[item_id]['need']) == 0 and table[item_id]['got_query_result'] == True:
            try:
                finished_set.add(item_id)
                final_result_item = table[item_id]
                del table[item_id]
            except KeyError:
                pass # Only the thread which deletes the item from the table is allowed to write it into the output
            else:
                out_queue.put({'result': final_result_item['result']})
                timestamp_queue.put({'timestamp': time.time()})
                logger.debug('Finished Result {}'.format(item_id))
        item = queue.get()
    logger.debug('Joined Result thread is done!')


def mp_validate(out_queue, shape_variables_queue, config, query, result_transmitter):
    """
    Function to be executed with Runner to run the validation process of the backend.
    """
    schema = prepare_validation(config, query, result_transmitter)

    # 1.) Identify Variables referring to shapes which we are going to validate.
    shape_variables_queue.put((query.target_var,))
    logger.debug("Query PV: {}".format(query.PV))
    for obj,pred in schema.shapesDict[config.target_shape].referencedShapes.items():
        logger.debug(str(config.target_shape) +", " + str(pred) + ", " + str(obj))
        new_shape_vars = query.get_variables_from_pred(pred)
        shape_variables_queue.put(new_shape_vars.intersection(query.PV))
    shape_variables_queue.put('EOF')
    logger.info("Done finding shape vars!")

    # 2.) Validate Schema
    # When using the default transmission_strategy, validation results will be put into the out_queue during validation
    report = schema.validate(config.start_with_target_shape)

    # The following only works with travshacl backend --> s2spy don't provide results after validation terminates.
    if not result_transmitter.use_streaming():
        for shape, instance_dict in report.items():
            for is_valid, instances in instance_dict.items():
                for instance in instances:
                    out_queue.put({'instance': instance[1], 'validation': (
                        instance[0], (is_valid == 'valid_instances'), shape)})
    # {instance: (shape of instance, is_valid, violating/validating shape)}
    # out_queue.put('EOF')

def mp_xjoin(left, right, out_queue, config):
    """
    Function to be executed with Runner to join the instances of the left with the right queue.
    """
    if config.join_implementation == 'Xjoin':
        Join = XJoin
    elif config.join_implementation == 'Xgjoin':
        Join = Xgjoin
    else:
        raise NotImplementedError("The given join {} is not implemented".format(config.join_implementation))
    
    join_instance = Join(['instance'], config.memory_size)
    join_instance.execute(left, right, out_queue)

# def proxy(in_queue, out_queue):
#     """
#     Debugging function to print the content of a queue during multiprocessing.
#     """
#     actual_tuple = in_queue.get()
#     while actual_tuple != 'EOF':
#         out_queue.put(actual_tuple)
#         print(str(actual_tuple))
#         actual_tuple = in_queue.get()
    # out_queue.put('EOF')

# Not needed anymore! (Integrated into contactSource)
# def contact_source_to_XJoin_Format(in_queue, out_queue, in_copy_queue):
#     """
#     Transforms contactSource Output to a format which is joinable with validation results.
#     Example:
#         Input: {var1: instance1, var2: instance2, var3: instance3}
#         Output:
#                {'instance': instance1, 'var': var1, 'id': UNIQUE_RESULT_ID},
#                {'instance': instance2, 'var': var2, 'id': UNIQUE_RESULT_ID},
#                {'instance': instance3, 'var': var3, 'id': UNIQUE_RESULT_ID}
#     """
#     actual_tuple = in_queue.get()
#     query_result_id = 0
#     while actual_tuple != 'EOF':
#         for var, instance in actual_tuple.items():
#             out_queue.put({'var': var, 'instance': instance, 'id': query_result_id})
#         in_copy_queue.put({'query_result': actual_tuple, 'id':query_result_id})
#         query_result_id = query_result_id + 1
#         actual_tuple = in_queue.get()
#     out_queue.put('EOF')
#     in_copy_queue.put('EOF')
