from app.utils import prepare_validation
import multiprocessing as mp
from app.query import Query

class Runner:
    def __init__(self,function, number_of_out_queues = 1, in_queues = list()):
        self.context   = mp.get_context("spawn")
        self.manager = mp.Manager()
        self.task_queue = self.context.Queue()
        self.out_queues = []
        for _ in range(number_of_out_queues):
            self.out_queues += [self.manager.Queue()]
        self.out_queues = tuple(self.out_queues)
        self.in_queues = tuple(in_queues)
        self.function = function
        self.process = self.context.Process(target=mp_function, args=(self.task_queue, self.function, self.in_queues, self.out_queues))
    
    def start_process(self):
        self.process.start()
    
    def stop_process(self):
        self.task_queue.put('EOF')
    
    def process_is_alive(self):
        return self.process.is_alive()
        
    def get_out_queues(self):
        return self.out_queues

    def new_task(self, *task):
        self.task_queue.put(task)

def mp_function(task_in_queue, function, in_queues, out_queues):
    speed_up_query = Query.prepare_query("PREFIX test1:<http://example.org/testGraph1#>\nSELECT DISTINCT ?x WHERE {\n?x a test1:classE.\n?x test1:has ?lit.\n}")
    speed_up_query.namespace_manager.namespaces()
    active_task = task_in_queue.get()
    while active_task != 'EOF':
        function(*in_queues, *out_queues, *active_task)
        active_task = task_in_queue.get()
