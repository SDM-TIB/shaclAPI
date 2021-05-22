import time
import warnings

from app.output.CSVWriter import CSVWriter
from app.output.statsOutput import StatsOutput


class StatsCalculation:

    def __init__(self, test_identifier, approach_name):
        self.test_name = test_identifier
        self.approach_name = approach_name.rsplit('.json', 1)[0]
        self.first_result_timestamp = None
        self.last_result_timestamp = None
        self.validation_finished_time = None
        self.query_finished_time = None
        self.join_finished_time = None
        self.join_started_time = None
        self.number_of_results = None
        self.post_processing_finished_time = None

    def globalCalculationStart(self):
        self.global_start_time = time.time()
    
    def globalCalculationFinished(self):
        self.global_end_time = time.time()
    
    def taskCalculationStart(self):
        self.task_start_time = time.time()

    def receive_and_write_trace(self, trace_file, timestamp_queue, queue_timeout):
        writer = CSVWriter(trace_file)
        received_results = 0
        result = timestamp_queue.get(timeout=queue_timeout)
        while result != 'EOF':
            received_results += 1
            writer.writeMulti({"test": self.test_name,
                               "approach": self.approach_name,
                               "answer": received_results,
                               "time": result['timestamp'] - self.global_start_time})
            self.last_result_timestamp = result['timestamp']
            if not self.first_result_timestamp:
                self.first_result_timestamp = result['timestamp']
            result = timestamp_queue.get(timeout=queue_timeout)
        self.number_of_results = received_results
        writer.close()

    def receive_global_stats(self, stats_out_queue, queue_timeout):
        needed_stats = {'mp_validate': False,
                        'contactSource': False,
                        'mp_xjoin': False,
                        'first_validation_result': False}
        while sum(needed_stats.values()) < len(needed_stats.keys()):
            statistic = stats_out_queue.get(timeout=queue_timeout)
            needed_stats[statistic['topic']] = True
            if statistic['topic'] == 'mp_validate':
                self.validation_finished_time = statistic['time']
            elif statistic['topic'] == 'contactSource':
                self.query_finished_time = statistic['time']
            elif statistic['topic'] == 'mp_xjoin':
                self.join_finished_time = statistic['time']            
            elif statistic['topic'] == 'first_validation_result':
                self.join_started_time = statistic['time']
            elif statistic['topic'] == 'mp_post_processing':
                self.post_processing_finished_time = statistic['time']
            elif statistic['topic'] == 'Exception':
                raise Exception("An Exception occurred in " + statistic['location'])
            else:
                raise Exception("received statistic with unknown topic: {}".format(statistic['topic']))

    def write_matrix_and_stats_files(self, matrix_file, stats_file):
        total_execution_time = self.global_end_time - self.global_start_time
        query_time = self.query_finished_time - self.task_start_time
        network_validation_time = self.validation_finished_time - self.task_start_time
        join_time = self.join_finished_time - self.join_started_time

        if self.first_result_timestamp:
            first_result_time = self.first_result_timestamp - self.global_start_time
        else: 
            first_result_time = "NaN"

        if self.last_result_timestamp:
            last_result_time = self.last_result_timestamp - self.global_start_time
        else:
            last_result_time = "NaN"

        matrix_entry = {"test": self.test_name,
                        "approach": self.approach_name,
                        "tfft": first_result_time,
                        "totaltime": last_result_time,
                        "comp": self.number_of_results}
        stats_entry = {"test": self.test_name,
                       "approach": self.approach_name,
                       "total_execution_time": total_execution_time,
                       "query_time": query_time,
                       "network_validation_time": network_validation_time,
                       "join_time": join_time}
        CSVWriter(matrix_file).writeSingle(matrix_entry)
        CSVWriter(stats_file).writeSingle(stats_entry)
        return StatsOutput(output=stats_entry)
