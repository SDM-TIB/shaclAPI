import multiprocessing as mp
import app.colors as Colors
from app.utils import prepare_validation
from app.multiprocessing.Xjoin import XJoin
import warnings, time


def queue_output_to_table(join_result_queue, query_queue, individual_result_times_queue=None):
    """
    Transforms the joined output and the raw query result to the final output. Therefore we need to find the singles (literals with no shape associated)
    1.) First gather joined Query Results (Query Result + Validation Result) with the same id  --> hashtable (dict)
    2.) Find singles (vars)
    3.) Extend the joined Query Results with the data from the query_queue for each single.
    Example:
    Input: 
        Query Queue: {'var': 'x', 'instance': 'http://example.org/testGraph3b#nodeA_0', 'id': 0}, {'var': 'lit', 'instance': 'literal', 'id': 0},...
        Joined Result Queue: {'instance': 'http://example.org/testGraph3b#nodeA_0', 'validation': ('ShapeA', True, 'unbound'), 'var': 'x', 'id': 0},...
    Output: [{'instance': 'http://example.org/testGraph3b#nodeA_0', 'validation': ('ShapeA', True, 'unbound'), 'var': 'x'}, {'var': 'lit', 'instance': 'literal'}], ...
    """
    # Step 1: Gather joined Query Results with the same id
    table = {}
    item = join_result_queue.get()
    number_of_results = 0
    while item != 'EOF':
        # A new result is received:
        if individual_result_times_queue:
            individual_result_times_queue.put({"topic": "new_xjoin_result", "time": time.time(), "validation_result": item['validation'][1]})
        number_of_results += 1
        item_id = item['id']
        del item['id']
        if item_id not in table:
            table[item_id] = []
        table[item_id] += [item]
        item = join_result_queue.get()
    if individual_result_times_queue:
        individual_result_times_queue.put({"topic": "number_of_results", "number": number_of_results})
        individual_result_times_queue.put('EOF')
    # Step 2: Find variables with no matching validation result
    singles = []
    item = query_queue.get()

    if item == 'EOF':
        print("Initial Query Bindings were empty!!")
        return list()
    
    item_id = item['id']
    del item['id']
    assert item_id in table
    for val_result in table[item_id]:
        try:
            del item['query_result'][val_result['var']]
        except:
            warnings.warn("Found duplicate Var!")
    for var, instance in item['query_result'].items():
        singles += [var]
        table[item_id] += [{'var': var, 'instance': instance}]

    # Step 3: Add Singles with instance to the matching joined validation result
    item = query_queue.get()
    while item != 'EOF':
        item_id = item['id']
        for single in singles:
            assert item_id in table
            table[item_id] += [{'var': single, 'instance': item['query_result'][single], 'validation': None}]
        item = query_queue.get()
    return list(table.values())

def mp_validate(out_queue, config, query, result_transmitter):
    """
    Function to be executed with Runner to run the validation process of the backend.
    """
    schema = prepare_validation(config, query, result_transmitter)
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
    join = XJoin(['instance'], config.memory_size)
    join.execute(left, right, out_queue)

def proxy(in_queue, out_queue):
    """
    Debugging function to print the content of a queue during multiprocessing.
    """
    actual_tuple = in_queue.get()
    while actual_tuple != 'EOF':
        out_queue.put(actual_tuple)
        print(Colors.yellow(str(actual_tuple)))
        actual_tuple = in_queue.get()
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
