import csv
import os
import time


class StatsCalculation:

    def __init__(self, test_identifier, approach_name):
        self.test_name = test_identifier
        self.approach_name = approach_name.rsplit('.json', 1)[0]

        self.first_result_timestamp = None
        self.last_result_timestamp = None

        self.validation_started_time = None
        self.validation_finished_time = None

        self.query_started_time = None
        self.query_finished_time = None

        self.join_started_time = None
        self.join_finished_time = None

        self.post_processing_started_time = None
        self.post_processing_finished_time = None

        self.first_validation_result_time = None
        self.number_of_results = 'Not Calculated'

        self.global_start_time = None
        self.global_end_time = None
        self.task_start_time = None

    def globalCalculationStart(self):
        self.global_start_time = time.time()
    
    def globalCalculationFinished(self):
        self.global_end_time = time.time()
    
    def taskCalculationStart(self):
        self.task_start_time = time.time()

    def receive_and_write_trace(self, trace_file, timestamp_queue):
        """
        This assigns the timestamp of the first and the last result; writes the trace file and counts the number of results.
        This is done using the path of the trace_file and the timestamp_queue (information from the post-processing step)
        """
        if trace_file is not None:
            f, writer = self._open_csv(trace_file, ['test', 'approach', 'answer', 'time'])
            
        received_results = 0
        result = timestamp_queue.get()
        while result != 'EOF':
            received_results += 1
            if trace_file is not None:
                writer.writerow({
                    "test": self.test_name,
                    "approach": self.approach_name,
                    "answer": received_results,
                    "time": result['timestamp'] - self.global_start_time
                })
            self.last_result_timestamp = result['timestamp']
            if not self.first_result_timestamp:
                self.first_result_timestamp = result['timestamp']
            result = timestamp_queue.get()
        self.number_of_results = received_results
        if trace_file is not None:
            f.close()

    @staticmethod
    def _open_csv(file, fields):
        mode = 'a' if os.path.isfile(file) else 'w'
        f = open(file, mode)
        writer = csv.DictWriter(f, fields)
        if mode == 'w':
            writer.writeheader()
        return f, writer

    def receive_global_stats(self, stats_out_queue, using_output_completion_runner=False):
        """
        Receiving start and stop times of the different steps and also the time  of the first validation result.
        """
        needed_stats = {'mp_validate': False,
                        'contactSource': False,
                        'mp_xjoin': False,
                        'mp_post_processing': False,
                        'first_validation_result': False}

        if using_output_completion_runner:
            needed_stats['mp_output_completion'] = False

        while sum(needed_stats.values()) < len(needed_stats.keys()):
            statistic = stats_out_queue.get()
            needed_stats[statistic['topic']] = True
            if statistic['topic'] == 'mp_validate':
                self.validation_started_time, self.validation_finished_time = statistic['time']
            elif statistic['topic'] == 'contactSource':
                self.query_started_time, self.query_finished_time = statistic['time']
            elif statistic['topic'] == 'mp_xjoin':
                self.join_started_time, self.join_finished_time = statistic['time']            
            elif statistic['topic'] == 'mp_post_processing':
                self.post_processing_started_time, self.post_processing_finished_time = statistic['time']
            elif statistic['topic'] == 'first_validation_result':
                self.first_validation_result_time = statistic['time']
            elif statistic['topic'] == 'mp_output_completion':
                _, self.global_end_time = statistic['time']
            elif statistic['topic'] == 'Exception':
                raise Exception("An Exception occurred in " + statistic['location'])
            else:
                raise Exception("received statistic with unknown topic: {}".format(statistic['topic']))

    def write_matrix_and_stats_files(self, matrix_file, stats_file):
        total_execution_time = self.global_end_time - self.global_start_time

        if self.query_started_time is not None and self.query_finished_time is not None:
            query_time = self.query_finished_time - self.query_started_time
        else:
            query_time = 'NaN'
        
        if self.validation_finished_time is not None and self.validation_started_time is not None:
            network_validation_time = self.validation_finished_time - self.validation_started_time
        else:
            network_validation_time = 'NaN'
        
        if self.post_processing_finished_time is not None and self.post_processing_started_time is not None:
            post_processing_time = self.post_processing_finished_time - self.post_processing_started_time
        else:
            post_processing_time = 'NaN'

        # Using the maximum of these timestamps because the later one better describes the "real" start of the join.
        if self.first_validation_result_time:
            approximated_join_start = max(self.join_started_time, self.first_validation_result_time)
        else: 
            approximated_join_start = self.join_started_time
        
        if self.join_started_time is not None and self.join_finished_time is not None:
            join_time = self.join_finished_time - approximated_join_start
        else:
            join_time = 'NaN'

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
        if matrix_file is not None:
            f, writer = self._open_csv(matrix_file, ['test', 'approach', 'tfft', 'totaltime', 'comp'])
            writer.writerow(matrix_entry)
            f.close()

        if stats_file is not None:
            f, writer = self._open_csv(stats_file, ['test', 'approach', 'total_execution_time', 'query_time', 'network_validation_time', 'join_time'])
            writer.writerow(stats_entry)
            f.close()
