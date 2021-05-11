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
    def __init__(self,function, number_of_out_queues = 1, in_queues = list(), runner_stats_out_queue=None):
        self.context   = mp.get_context("spawn")
        self.manager = mp.Manager()
        self.out_queues = []
        for _ in range(number_of_out_queues):
            self.out_queues += [self.manager.Queue()]
        self.out_queues = tuple(self.out_queues)
        self.in_queues = tuple(in_queues)
        if not runner_stats_out_queue:
            self.stats_out_queue = self.manager.Queue()
        else:
            self.stats_out_queue = runner_stats_out_queue
        self.function = function
    
    def start_process(self):
        self.task_queue = self.context.Queue()
        self.process = mp.Process(target=mp_function, args=(self.task_queue, self.function, self.in_queues, self.out_queues, self.stats_out_queue))
        self.process.start()
    
    def stop_process(self):
        self.process.terminate()
    
    def process_is_alive(self):
        return self.process.is_alive()
        
    def get_out_queues(self):
        return *self.out_queues, self.stats_out_queue

    def new_task(self, *task):
        print(self.function.__name__,"new task put")
        self.task_queue.put(task)

    def clear_queues(self):
        self.clear_queue(self.stats_out_queue)
        for q in self.out_queues:
           self.clear_queue(q)
        for q in self.in_queues:
           self.clear_queue(q)

    
    def clear_queue(self,queue):
        print("Clear queue!", str(queue))
        while True:
            try:
                queue.get(timeout=0.5)
            except:
                break


def mp_function(task_in_queue, function, in_queues, out_queues, stats_out_queue):
    speed_up_query = Query.prepare_query("PREFIX test1:<http://example.org/testGraph1#>\nSELECT DISTINCT ?x WHERE {\n?x a test1:classE.\n?x test1:has ?lit.\n}")
    speed_up_query.namespace_manager.namespaces()
    try:
        print(function.__name__, "started!")
        active_task = task_in_queue.get()
        print(function.__name__, "received first task!")
        while active_task != 'EOF':
            try:
                function(*in_queues, *out_queues, *active_task[1:])
            except Exception as e:
                stats_out_queue.put({"topic": "Exception", "location": function.__name__})
                print(e)
            finally:
                for queue in out_queues:
                    queue.put('EOF') # Writing EOF here allows global error handling
                finished_timestamp = time.time()
                if active_task[0]:
                    stats_out_queue.put({"topic": function.__name__, "time": finished_timestamp})
                active_task = task_in_queue.get()
    except KeyboardInterrupt:
        pass
