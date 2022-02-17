import json
import uuid


class Config:
    def __init__(self, config_dict):
        self.config_dict = config_dict
        self.INTERNAL_SPARQL_ENDPOINT = "http://localhost:5000/endpoint"
        self.check()

    @staticmethod
    def from_request_form(request_params):
        config_file_path = request_params.get('config')
        if config_file_path != None:
            with open(config_file_path) as config_file:
                final_config = json.load(config_file)
            final_config.update(request_params)
        else:
            final_config = dict()
            final_config.update(request_params)
        return Config(final_config)

    @staticmethod
    def entry_to_bool(item):
        if type(item) == bool:
            return item
        else:
            if item == 'True':
                return True
            elif item == 'False':
                return False
            else:
                raise Exception("Could not interprete {}".format(item))

    def check(self):
        if self.backend == "s2spy" and self.start_with_target_shape == False:
            raise Exception("backend s2spy needs to start with target shape; set start_with_target_shape to True")
        if self.prune_shape_network == False and self.remove_constraints:
            raise Exception("Its not possible to not prune the shape network but removing constraints (impling pruning the shape network...)")
        if self.use_pipes and self.run_in_serial:
            raise Exception("Pipes can only hold a limited amount of data and can therefore not be used in serial mode.")

    # ------------------------------- required configuration options -------------------------------------------
    @property
    def query(self):
        """
        The starshaped query to be executed.
        """
        return self.config_dict['query']

    @property
    def target_shape(self):
        """
        The target shape to which the star shaped query refers.
        """
        return self.config_dict.get('targetShape', None)

    @property
    def external_endpoint(self):
        """
        The external sparql endpoint, which contains the data to be validated.
        """
        return self.config_dict['external_endpoint']

    @property
    def schema_directory(self):
        """
        The directory which contains the shape files.
        """
        return self.config_dict['schemaDir']

    # ------------------------------- optional configuration options (there are default values) -------------------------------------------
    @property
    def config(self):
        """
        config is the absolute or relativ (with respect to the location of run.py) path to a configuration file.
        --> The Configuration file is json-formated file which can include the same options as the POST - Request.
        --> The Options specified in the POST - Request will override the options in the configuration file.
        """
        return self.config_dict.get('config', 'config')

    @property
    def save_outputs(self):
        """
        Whether to save the validation output of the backend to a file.
        """
        return self.entry_to_bool(self.config_dict.get('outputs', False))

    @property
    def output_directory(self):
        """
        The directory which will be used by the backend and the api to save the validation output and statistics to files (depending on the other configurations)
        """
        return self.config_dict.get('output_directory') or self.config_dict.get('outputDirectory') or "./output/"

    @property
    def schema_format(self):
        """
        The format of the shape files. Only JSON is supported.
        """
        return self.config_dict.get('shape_format') or \
            self.config_dict.get('shapeFormat') or \
            self.config_dict.get('schema_format') or \
            "JSON"

    @property
    def work_in_parallel(self):
        """
        Whether the backend should work in parallel.
        """
        return self.entry_to_bool(self.config_dict.get('work_in_parallel', False)) or \
            self.entry_to_bool(self.config_dict.get('workInParallel', False)) or \
            False

    @property
    def use_selective_queries(self):
        """
        The travshacl backend can use more selectiv queries. This options is used to turn that on or off.
        """
        return self.entry_to_bool(self.config_dict.get('useSelectiveQueries', True))

    @property
    def max_split_size(self):
        """
        The max split size.
        """
        return int(self.config_dict.get('maxSplit', 256))

    @property
    def order_by_in_queries(self):
        """
        Whether to use Queries with a ORDER BY Clause.
        """
        return self.entry_to_bool(self.config_dict.get('ORDERBYinQueries', True))

    @property
    def SHACL2SPARQL_order(self):
        """
        Whether to use the SHACL2SPARQL_order. (TODO: Not used in either case)
        """
        return self.entry_to_bool(self.config_dict.get('SHACL2SPARQLorder', False))

    @property
    def debugging(self):
        """
        Whether debugging mode is active. When using debugging mode the api is working as a proxy between the
        external endpoint and the backend; which allows writing received queries to the standard output.
        """
        return self.entry_to_bool(self.config_dict.get('debugging', False))

    @property
    def backend(self):
        """
        The backend to use. Only "travshacl" or "s2spy" is implemented.
        """
        return self.config_dict.get('backend', "travshacl")

    @property
    def task(self):
        """
        The task to be done by the backend. (TODO: Only 'a' makes sense here.)
        """
        return self.config_dict.get('task', 'a')

    @property
    def traversal_strategy(self):
        """
        The traversal strategy used by the backend to reduce the shape graph and by the backend
        to find the execution order. Can be "DFS" or "BFS".
        """
        return self.config_dict.get('traversalStrategy') or 'DFS'

    @property
    def heuristic(self):
        """
        Heuristics which the travshacl backend should use.
        """
        return self.config_dict.get('heuristic') or 'TARGET IN BIG'

    @property
    def replace_target_query(self):
        """
        Whether or not the api should replace the target query of the target shape.
        """
        return self.entry_to_bool(self.config_dict.get('replace_target_query', True))

    @property
    def merge_old_target_query(self):
        """
        Whether the api should merge the star shaped query with the given target query in the target shape file.
        If this option is inactive the target query of the target shape is basically replaced with the star shaped query.
        """
        return self.entry_to_bool(self.config_dict.get('merge_old_target_query', True))

    @property
    def start_with_target_shape(self):
        """
        Whether the backend is forced to start the validation process with the target shape.
        """
        return self.entry_to_bool(self.config_dict.get('start_with_target_shape', True))

    @property
    def start_shape_for_validation(self):
        """
        The shape which is used as starting point for the validation in the backend.
        (it will override the start point determined by the backend (in case of travshacl) and only applies if start_with_target_shape is false)
        """
        return self.config_dict.get('start_shape_for_validation', None)

    @property
    def remove_constraints(self):
        """
        Whether the api should remove constraints of the target shape not mentioned in the query.
        """
        return self.entry_to_bool(self.config_dict.get('remove_constraints', False))

    @property
    def send_initial_query_over_internal_endpoint(self):
        """
        There might be problems with contactSource and some Sparql Endpoints. These can be fixed by routing through our internal endpoint.
        This will force the api todo so.
        """
        return self.entry_to_bool(self.config_dict.get('send_initial_query_over_internal_endpoint', False))

    @property
    def output_format(self):
        """
        Which output format the api should use. This can be "test", "stats" or "simple"
        """
        return self.config_dict.get('output_format', "simple")

    @property
    def memory_size(self):
        """
        Number of tuples which can be stored in main memory
        """
        return int(self.config_dict.get('memory_size', 100000000))

    @property
    def prune_shape_network(self):
        """
        Whether or not prune the shape_network to the from the target shape reachable shapes.
        """
        return self.entry_to_bool(self.config_dict.get('prune_shape_network', True))

    @property
    def test_identifier(self):
        """
        The test identifier will be used in output files / Stats Output identifying the test run.
        """
        return self.config_dict.get('test_identifier', str(uuid.uuid1()))

    @property    
    def run_in_serial(self):
        """
        This option can be turned on to force the multiprocessing steps to be executed in serial.
        This option is only used in multiprocessing route.
        """
        return self.entry_to_bool(self.config_dict.get('run_in_serial', False))
    
    @property
    def reasoning(self):
        """
        This option will turn reasoning in terms of extended output on and off. Default is on.
        """
        return self.entry_to_bool(self.config_dict.get('reasoning', True))
    
    @property
    def use_pipes(self):
        """
        Whether to use Pipes or not (in that case Queues are used)
        """
        return self.entry_to_bool(self.config_dict.get('use_pipes', False))
    
    @property
    def collect_all_validation_results(self):
        """
        Whether to collect all validation results for each mapping or at least one of the target_shape and one for each other mapping.
        Collecting all results will make the approach blocking.
        """
        return self.entry_to_bool(self.config_dict.get('collect_all_validation_results', False))

    # --------------------- Calculated Configs --------------------------------------------------
    @property
    def internal_endpoint(self):
        return self.INTERNAL_SPARQL_ENDPOINT if self.debugging else self.external_endpoint
