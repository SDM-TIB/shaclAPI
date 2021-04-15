import multiprocessing as mp
import app.colors as Colors
from app.utils import prepare_validation
from app.multiprocessing.Xjoin import XJoin
import warnings

# Not needed anymore! (Integrated into contactSource)
# def contact_source_to_XJoin_Format(in_queue, out_queue, in_copy_queue):
#     '''
#     Transforms contactSource Output to a format which is joinable with validation results. 
#     Example:
#         Input: {var1: instance1, var2: instance2, var3: instance3} 
#         Output:
#                {'instance': instance1, 'var': var1, 'id': UNIQUE_RESULT_ID}, 
#                {'instance': instance2, 'var': var2, 'id': UNIQUE_RESULT_ID}, 
#                {'instance': instance3, 'var': var3, 'id': UNIQUE_RESULT_ID}
#     '''
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

def queue_output_to_table(join_result_queue, query_queue):
    '''
    Transforms the joined output and the raw query result to the final output. Therefore we need to find the singles (literals with no shape associated)
    1.) First gather joined Query Results with the same id  --> hashtable (dict)
    2.) Find singles
    3.) Extend each result with the data from the query_queue
    Example:
    Input: 
        Query Queue: {'var': 'x', 'instance': 'http://example.org/testGraph3b#nodeA_0', 'id': 0}, {'var': 'lit', 'instance': 'literal', 'id': 0},...
        Joined Result Queue: {'instance': 'http://example.org/testGraph3b#nodeA_0', 'validation': ('ShapeA', True, 'unbound'), 'var': 'x', 'id': 0},...
    Output: [{'instance': 'http://example.org/testGraph3b#nodeA_0', 'validation': ('ShapeA', True, 'unbound'), 'var': 'x'}, {'var': 'lit', 'instance': 'literal'}], ...
        
    '''
    # Step 1: Collect Query Results
    table = {}
    for item in queue_iter(join_result_queue):
        item_id = item['id']
        del item['id']
        if item_id not in table:
            table[item_id] = []
        table[item_id] += [item]
    
    # Step 2: Find singles with no matching validation result
    singles = []

    item = query_queue.get()
    item_id = item['id']
    del item['id']
    assert item_id in table
    # print(list(item['query_result'].keys()))
    for val_result in table[item_id]:
        # print('Trying to remove:' + val_result['var'])
        try:
            del item['query_result'][val_result['var']]
        except:
            warnings.warn("Found duplicate Var!")
    for var, instance in item['query_result'].items():
        singles += [var]
        table[item_id] += [{'var': var, 'instance': instance}]

    # Step 3: Add Singles with instance to the matching joined validation result
    for item in queue_iter(query_queue):
        item_id = item['id']
        for single in singles:
            table[item_id] += [{'var': single, 'instance': item['query_result'][single], 'validation': None}]
    return list(table.values())

def queue_iter(in_queue):
    # Do not use in multiprocessing context!
    actual_tuple = in_queue.get()
    while actual_tuple != 'EOF':
        yield actual_tuple
        actual_tuple = in_queue.get()

def proxy(in_queue, out_queue):
    actual_tuple = in_queue.get()
    while actual_tuple != 'EOF':
        out_queue.put(actual_tuple)
        print(Colors.yellow(str(actual_tuple)))
        actual_tuple = in_queue.get()
    out_queue.put('EOF')

def mp_validate(out_queue, query, replace_target_query,start_with_target_shape, merge_old_target_query, backend, result_transmitter, *params):
    schema = prepare_validation(query,replace_target_query, merge_old_target_query, *params, result_transmitter=result_transmitter, backend=backend)
    report = schema.validate(start_with_target_shape)
    if not result_transmitter.use_streaming(): # The following only works with travshacl backend --> s2spy don't provide results after validation terminates.
        for shape, instance_dict in report.items():
            for is_valid, instances in instance_dict.items():
                for instance in instances:
                    out_queue.put({'instance': instance[1], 'validation': (instance[0], (is_valid == 'valid_instances'), shape)})
    out_queue.put('EOF')  #{instance: (shape of instance, is_valid, violating/validating shape)}

def mp_xjoin(left, right, out_queue):
    join = XJoin(['instance'])
    join.execute(left, right, out_queue)