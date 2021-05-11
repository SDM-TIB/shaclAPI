import multiprocessing as mp
from app.query import Query
import time

class Runner:
    """
    A runner object is associated with a multiprocessing.Process which is started with start_process and runs until stop_process is called.
    Additional a runner has a function f assigned, which is executed each time when new_task is called.
    f needs to have to following parameters: 
        - FIRST: in_queues (multiprocessing.Queue)
        - SECOND: out_queues (number_of_out_queues specified in constructor of Runner)
        - FINALLY: variable number of parameters needed for the task (These ones which also needed to be passed to new_task)
    """
    def __init__(self,function, number_of_out_queues = 1):
        self.context   = mp.get_context("spawn")
        self.manager = mp.Manager()
        self.function = function
        self.number_of_out_queues = number_of_out_queues
        self.process = None
        self.task_queue = None
    
    def start_process(self):
        if self.process == None or not self.process_is_alive():
            self.task_queue = self.context.Queue()
            self.process = mp.Process(target=mp_function, args=(self.task_queue, self.function))
            self.process.start()
    
    def stop_process(self):
        if self.process_is_alive():
            self.task_queue.close()
            self.process.terminate()
            print("Process {} stopped!".format(self.function.__name__))
    
    def process_is_alive(self):
        return self.process.is_alive()
    
    def get_stats_out_queue(self):
        return self.manager.Queue()
    
    def get_new_out_queues(self):
        out_queues = []
        for _ in range(self.number_of_out_queues):
            out_queues += [self.manager.Queue()]
        out_queues = tuple(out_queues)
        return out_queues

    def new_task(self, in_queues, out_queues, task_description, runner_stats_out_queue):
        if self.process_is_alive():
            self.task_queue.put((in_queues, out_queues, runner_stats_out_queue, task_description))
        else:
            raise Exception("Start processes before using /multiprocessing")

def mp_function(task_in_queue, function):
    speed_up_query = Query.prepare_query("PREFIX test1:<http://example.org/testGraph1#>\nSELECT DISTINCT ?x WHERE {\n?x a test1:classE.\n?x test1:has ?lit.\n}")
    speed_up_query.namespace_manager.namespaces()
    try:
        print("Process", function.__name__, "started!")
        active_task = task_in_queue.get()
        while active_task != 'EOF':
            in_queues, out_queues, runner_stats_out_queue, task_description = active_task
            try:
                function(*in_queues, *out_queues, *task_description)
            except Exception as e:
                runner_stats_out_queue.put({"topic": "Exception", "location": function.__name__})
                print(e)
            finally:
                for queue in out_queues:
                    queue.put('EOF') # Writing EOF here allows global error handling
                finished_timestamp = time.time()
                runner_stats_out_queue.put({"topic": function.__name__, "time": finished_timestamp})
                active_task = task_in_queue.get()
    except KeyboardInterrupt:
        pass
