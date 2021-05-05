import time, json

class StatsOutput():
    def __init__(self, output={}):
        self._output = output
    
    def to_json(self,targetShapeID):
        return json.dumps(self._output)
    
    @staticmethod
    def from_queues(global_start_time, task_start_time, stats_out_queue_contact, stats_out_queue_val, stats_out_queue_xjoin):
        query_finished_time = stats_out_queue_contact.get()
        validation_finished_time = stats_out_queue_val.get()
        join_started_time = stats_out_queue_xjoin.get()
        join_finished_time = stats_out_queue_xjoin.get()
        end_time = time.time()
        return StatsOutput(output={"total_execution_time": end_time - global_start_time, "query_time": query_finished_time - task_start_time, "network_validation_time": validation_finished_time - task_start_time, "join_time": join_finished_time - join_started_time})
