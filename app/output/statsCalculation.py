import time
from app.output.statsOutput import StatsOutput
from app.output.CSVWriter import CSVWriter
import warnings
import math

class StatsCalculation():
    def __init__(self, test_identifier, approach_name):
        self.test_name = test_identifier
        self.approach_name = approach_name
        self.first_result_timestamp = None
        self.last_result_timestamp = None
        self.number_of_results = None
        self.validation_finished_time = None
        self.query_finished_time = None
        self.join_finished_time = None
        self.join_started_time = None

    def globalCalculationStart(self):
        self.global_start_time = time.time()
    
    def globalCalculationFinished(self):
        self.global_end_time = time.time()
    
    def taskCalculationStart(self):
        self.task_start_time = time.time()

    def receive_and_write_trace(self, trace_file, individual_result_times_queue):
        writer = CSVWriter(trace_file)
        print('receive_and_write_trace started!')
        result_stat = individual_result_times_queue.get()
        received_results = 0
        while result_stat != 'EOF':
            if result_stat['topic'] ==  'new_xjoin_result':
                received_results += 1
                writer.writeMulti({"test_name": self.test_name, "approach": self.approach_name, "time": result_stat['time'] - self.global_start_time, "validation": 'valid' if result_stat['validation_result'] else 'invalid'})
                self.last_result_timestamp = result_stat['time']
                if not self.first_result_timestamp:
                    self.first_result_timestamp = result_stat['time']
            elif result_stat['topic'] == 'number_of_results':
                self.number_of_results = result_stat['number']
            else: 
                raise Exception("received statistic with unknown topic")
            result_stat = individual_result_times_queue.get()
        if self.number_of_results != received_results:
            warnings.warn("Number of Result timestamps received is not equal to the number of results!")
        writer.close()
        print('receive_and_write_trace finished!')

    
    def receive_global_stats(self, stats_out_queue):
        print('receive_global_stats started!')
        needed_stats = {'mp_validate': False, 'contactSource': False, 'mp_xjoin': False, 'first_validation_result': False }
        while sum(needed_stats.values()) < len(needed_stats.keys()):
            statistic = stats_out_queue.get()
            needed_stats[statistic['topic']] = True
            if statistic['topic'] == 'mp_validate':
                self.validation_finished_time = statistic['time']
            elif statistic['topic'] == 'contactSource':
                self.query_finished_time = statistic['time']
            elif statistic['topic'] == 'mp_xjoin':
                self.join_finished_time = statistic['time']            
            elif statistic['topic'] == 'first_validation_result':
                self.join_started_time = statistic['time']
            elif statistic['topic'] == 'Exception':
                raise Exception("An Exception occured in " + statistic['location'])
            else:
                raise Exception("received statistic with unknown topic")
        print('receive_global_stats stopped!')


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

        matrix_entry = {"test_name": self.test_name, "approach": self.approach_name, "first_result_time": first_result_time, "last_result_time": last_result_time, "number_of_results": self.number_of_results}
        stats_entry = {"test_name": self.test_name, "approach": self.approach_name, "total_execution_time": total_execution_time, "query_time": query_time, "network_validation_time": network_validation_time, "join_time": join_time}
        CSVWriter(matrix_file).writeSingle(matrix_entry)
        CSVWriter(stats_file).writeSingle(stats_entry)
        return StatsOutput(output=stats_entry)