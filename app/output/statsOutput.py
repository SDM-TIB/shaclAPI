import time, json

class StatsOutput():
    def __init__(self, output={}):
        self._output = output
    
    def to_json(self,targetShapeID):
        return json.dumps(self._output)
    
    @property
    def output(self):
        return self._output
    
    @staticmethod
    def from_queues(test_identifier, approach_name, global_start_time, task_start_time, stats_out_queue_contact, stats_out_queue_val, stats_out_queue_xjoin):
        global_end_time = time.time()
        query_finished_time = stats_out_queue_contact.get()['time']
        validation_finished_time = stats_out_queue_val.get()['time']

        first_result_timestamp = None
        last_result_timestamp = None
        number_of_results = None
        join_finished_time = None
        test_name = test_identifier
        approach_name = approach_name
        traces = []


        join_stat = stats_out_queue_xjoin.get()
        while join_stat != 'EOF':
            if join_stat['topic'] ==  'new_xjoin_result':
                traces += [{"test_name": test_name, "approach": approach_name, "time": join_stat['time'] - global_start_time, "validation": 'valid' if join_stat['validation_result'] else 'invalid'}]
                last_result_timestamp = join_stat['time']
                if not first_result_timestamp:
                    first_result_timestamp = join_stat['time']
            elif join_stat['topic'] == 'number_of_results':
                number_of_results = join_stat['number']
            elif join_stat['topic'] == 'first_validation_result':
                join_started_time = join_stat['time']
            else: 
                join_finished_time = join_stat['time']
            join_stat = stats_out_queue_xjoin.get()
        
        if not join_finished_time:
            join_finished_time = stats_out_queue_xjoin.get()['time']

        total_execution_time = global_end_time - global_start_time
        query_time = query_finished_time - task_start_time
        network_validation_time = validation_finished_time - task_start_time
        join_time = join_finished_time - join_started_time

        first_result_time = first_result_timestamp - global_start_time
        last_result_time = last_result_timestamp - global_start_time
        
        matrix = {"test_name": test_name, "approach": approach_name, "first_result_time": first_result_time, "last_result_time": last_result_time, "number_of_results": number_of_results}
        stats = {"test_identifier": test_identifier, "total_execution_time": total_execution_time, "query_time": query_time, "network_validation_time": network_validation_time, "join_time": join_time}

        return StatsOutput(output=stats), matrix, traces
