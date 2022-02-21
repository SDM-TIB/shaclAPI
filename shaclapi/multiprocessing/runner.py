import multiprocessing as mp
from shaclapi.query import Query
import time, atexit
import logging 
from shaclapi.multiprocessing.PipeAdapter import PipeAdapter, QueueAdapter

logger = logging.getLogger(__name__)

class Runner:
    """
    A runner object is associated with a multiprocessing.Process which is started with start_process and runs until stop_process is called.
    Additional a runner has a function f assigned, which is executed each time when new_task is called.
    f needs to have to following parameters: 
        - FIRST: in_queues (multiprocessing.Queue)
        - SECOND: out_queues (number_of_out_queues specified in constructor of Runner)
        - FINALLY: variable number of parameters needed for the task (These ones which also needed to be passed to new_task)
    """
    def __init__(self, function, number_of_out_queues = 1):
        self.context   = mp.get_context("spawn")
        self.manager = mp.Manager()
        self.function = function
        self.number_of_out_queues = number_of_out_queues
        self.process = None
        self.task_queue = None
        self.process_running = False
    
    def start_process(self):
        self.task_queue = self.context.Queue()
        self.process = mp.Process(target=mp_function, args=(self.task_queue, self.function), name=self.function.__name__ )
        self.process.start()
        self.process_running = True
        logger.info("Process {} started!".format(self.function.__name__))
        atexit.register(self.stop_process)

    def stop_process(self):
        if self.process and self.process_running:
            atexit.unregister(self.stop_process)
            self.task_queue.close()
            self.process.terminate()
            self.process = None
            self.process_running = False
            logger.info("Process {} stopped!".format(self.function.__name__))
    
    def get_new_queue(self):
        return self.manager.Queue()
    
    def get_new_out_queues(self, use_pipes):
        out_queues = []
        for _ in range(self.number_of_out_queues):
            if use_pipes:
                out_queues += [PipeAdapter()]
            else:
                out_queues += [QueueAdapter(self.manager)]
        out_queues = tuple(out_queues)
        return out_queues

    def new_task(self, in_queues, out_queues, task_description, runner_stats_out_queue, wait_for_finish=False):
        if self.process and self.process_running:
            if wait_for_finish:
                task_finished_recv, task_finished_send = self.context.Pipe()
                self.task_queue.put((in_queues, out_queues, runner_stats_out_queue, task_description, task_finished_send))
                result = task_finished_recv.recv()
                task_finished_send.close()
                task_finished_recv.close()
                return result
            else:
                self.task_queue.put((in_queues, out_queues, runner_stats_out_queue, task_description, None))
        else:
            raise Exception("Start processes before using /multiprocessing")

def mp_function(task_in_queue, function):
    speed_up_query = Query.prepare_query("PREFIX test1:<http://example.org/testGraph1#>\nSELECT DISTINCT ?x WHERE {\n?x a test1:classE.\n?x test1:has ?lit.\n}")
    speed_up_query.namespace_manager.namespaces()
    try:
        active_task = task_in_queue.get()
        while active_task != 'EOF':
            in_queues, out_queues, runner_stats_out_queue, task_description, task_finished_send = active_task

            # Now one can use logging as normal
            logger.info(function.__name__ + " received task!")
            try:
                start_timestamp = time.time()
                function(*in_queues, *out_queues, *task_description)
            except Exception as e:
                runner_stats_out_queue.put({"topic": "Exception", "location": function.__name__})
                logger.exception(e)
            finally:
                for queue in out_queues:
                    queue.put('EOF') # Writing EOF here allows global error handling
                finished_timestamp = time.time()
                runner_stats_out_queue.put({"topic": function.__name__, "time": (start_timestamp, finished_timestamp)})
                logger.info(function.__name__ + " finished task; waiting for next one!")
                if task_finished_send:
                    task_finished_send.send("Done")
                active_task = task_in_queue.get()
    except KeyboardInterrupt:
        pass
