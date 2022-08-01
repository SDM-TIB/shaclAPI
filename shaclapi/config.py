import json
import uuid


class Config:
    def __init__(self, config_dict):
        self.config_dict = config_dict
        self.check()

    @staticmethod
    def from_request_form(request_params):
        config_file_path = request_params.get('config')
        if config_file_path is not None:
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
                raise Exception("Could not interpret {}".format(item))

    def check(self):
        if self.backend == "s2spy" and not self.start_with_target_shape:
            raise Exception("backend s2spy needs to start with the target shape; set start_with_target_shape to True")
        if not self.prune_shape_network and self.remove_constraints:
            raise Exception("It's not possible to not prune the shape network but removing constraints (impling pruning the shape network...)")
        if self.use_pipes and self.run_in_serial:
            raise Exception("Pipes can only hold a limited amount of data and can therefore not be used in serial mode.")

    # ------------------------------- required configuration options -------------------------------------------
    @property
    def query(self):
        """
        The query to be executed over the SPARQL endpoint.
        """
        if 'query' in self.config_dict:
            return self.config_dict['query']
        else:
            raise Exception('The query to be executed over the SPARQL endpoint needs to be provided to the shaclAPI using the option query.')

    @property
    def external_endpoint(self):
        """
        The URL of the SPARQL endpoint, which contains the data to be validated and retrieved.
        """
        if 'external_endpoint' in self.config_dict:
            return self.config_dict['external_endpoint']
        else:
            raise Exception('The URL of the SPARQL endpoint the shape schema will be validated against and data retrieved, needs to be provided to the shaclAPI using the option external_endpoint.')

    @property
    def schema_directory(self):
        """
        The directory containing the shape files (.ttl or .json)
        """
        if 'schemaDir' in self.config_dict:        
            return self.config_dict['schemaDir']
        elif 'schema_directory' in self.config_dict:
            return self.config_dict['schema_directory']
        else:
            raise Exception('A directory containing the shape files needs to be provided to the shaclAPI using the option schema_directory or schema_directory!')

    # -------------------------- optional configuration options (there are default values) --------------------------
    @property
    def target_shape(self):
        """
        The target shape selected for the given query and the given shape schema.
        """
        if 'targetShape' in self.config_dict:
            return self.config_dict['targetShape']
        elif 'target_shape' in self.config_dict:
            return self.config_dict['target_shape']
        else:
            return None

    @target_shape.setter
    def target_shape(self, target_shape):
        self.config_dict['targetShape'] = target_shape

    @property
    def config(self):
        """
        The path to a json formatted configuration file. Has to be absolute or relative w.r.t. run.py.
        The file can include all the properties in :py:mod:`shaclapi.config` as configuration options.
        The options which are specified in the HTTP POST - request will override the options configured in the configuration file.
        """
        if 'config' in self.config_dict:
            return self.config_dict['config']
        else:
            return None

    @property
    def save_outputs(self):
        """
        Whether to save the validation output of the backend to a file.
        """
        return self.entry_to_bool(self.config_dict.get('outputs', False))

    @property
    def output_directory(self):
        """The directory which will be used by the SHACL engine and the shaclAPI to save the validation output and statistics to files (depending on the other configurations)
        """
        if 'outputDirectory' in self.config_dict:
            return self.config_dict['outputDirectory']
        elif 'output_directory' in self.config_dict:
            return self.config_dict['output_directory']
        else:
            return "./output/"

    @property
    def schema_format(self):
        """
        The format of the shape files. Can be JSON or TTL
        """
        if 'shapeFormat' in self.config_dict:
            return self.config_dict['shapeFormat']
        elif 'shape_format' in self.config_dict:
            return self.config_dict['shape_format']
        elif 'schema_format' in self.config_dict:
            return self.config_dict['schema_format']
        else:
            return "JSON"

    @property
    def work_in_parallel(self):
        """
        Whether the SHACL engine should work in parallel
        """
        if 'workInParallel' in self.config_dict:
            return self.entry_to_bool(self.config_dict['workInParallel'])
        elif 'work_in_parallel' in self.config_dict:
            return self.entry_to_bool(self.config_dict['work_in_parallel'])
        else:
            return False

    @property
    def use_selective_queries(self):
        """
        Whether the SHACL engine should use more selective queries.
        """
        if 'useSelectiveQueries' in self.config_dict:
            return self.entry_to_bool(self.config_dict['useSelectiveQueries'])
        elif 'use_selective_queries' in self.config_dict:
            return self.entry_to_bool(self.config_dict['use_selective_queries'])
        else:
            return True

    @property
    def max_split_size(self):
        """
        The maximal number of entities in FILTER or VALUES clause of a SPARQL query, used by the SHACL engine.
        """
        return int(self.config_dict.get('maxSplit', 256))

    @property
    def order_by_in_queries(self):
        """
        Whether the SHACL engine should use queries with a ORDER BY clause.
        """
        if 'ORDERBYinQueries' in self.config_dict:
            return self.entry_to_bool(self.config_dict['ORDERBYinQueries'])
        elif 'order_by_in_queries' in self.config_dict:
            return self.entry_to_bool(self.config_dict['order_by_in_queries'])
        else:
            return True

    @property
    def backend(self):
        """
        The SHACL engine, which will be used by the shaclAPI. Can be "travshacl" or "s2spy".
        """
        return self.config_dict.get('backend', "travshacl")

    @property
    def traversal_strategy(self):
        """
        The traversal strategy used by the backend to reduce the shape graph and by the backend
        to find the execution order. Can be "DFS" or "BFS".
        """
        if 'traversalStrategy' in self.config_dict:
            return self.config_dict.get('traversalStrategy')
        elif 'traversal_strategy' in self.config_dict:
            return self.config_dict.get('traversal_strategy')
        else: 
            return 'DFS'

    @property
    def heuristic(self):
        """
        Only if Trav-SHACL is used as backend. The heuristic used to determine the validation order of the shapes.
        """
        return self.config_dict.get('heuristic') or 'TARGET IN BIG'

    @property
    def replace_target_query(self):
        """
        Whether the shaclAPI should replace the target query of the target shape.
        """
        return self.entry_to_bool(self.config_dict.get('replace_target_query', True))

    @replace_target_query.setter
    def replace_target_query(self, replace):
        self.config_dict['replace_target_query'] = replace

    @property
    def merge_old_target_query(self):
        """
        Whether the shaclAPI should merge the star shaped query with the given target query in the target shape file.
        If this option is inactive the target query of the target shape is basically replaced with the star shaped query.
        """
        return self.entry_to_bool(self.config_dict.get('merge_old_target_query', True))

    @merge_old_target_query.setter
    def merge_old_target_query(self, merge):
        self.config_dict['merge_old_target_query'] = merge

    @property
    def start_with_target_shape(self):
        """
        Whether the SHACL engine is forced to start the validation process with the target shape.
        """
        return self.entry_to_bool(self.config_dict.get('start_with_target_shape', True))

    @start_with_target_shape.setter
    def start_with_target_shape(self, start):
        self.config_dict['start_with_target_shape'] = start

    @property
    def start_shape_for_validation(self):
        """
        The shape which is used as starting point for the validation in the backend. It will override the start point determined by the SHACL engine (in case of Trav-SHACL) and only applies if :attr:`start_with_target_shape` is false).
        """
        return self.config_dict.get('start_shape_for_validation', None)

    @property
    def remove_constraints(self):
        """
        Whether the shaclAPI should remove constraints of the target shape not mentioned in the query.
        """
        return self.entry_to_bool(self.config_dict.get('remove_constraints', False))

    @property
    def output_format(self):
        """
        Which output format the shaclAPI should use. This can be "test" or "simple".
        """
        return self.config_dict.get('output_format', "simple")

    @property
    def memory_size(self):
        """
        Number of tuples, which can be stored in main memory during the join process.
        """
        return int(self.config_dict.get('memory_size', 100000000))

    @property
    def prune_shape_network(self):
        """
        Whether prune the shape schema to the shapes reachable from the target shapes.
        """
        return self.entry_to_bool(self.config_dict.get('prune_shape_network', True))

    @prune_shape_network.setter
    def prune_shape_network(self, prune):
        self.config_dict['prune_shape_network'] = prune

    @property
    def test_identifier(self):
        """
        The test identifier will be used in output files identifying the run.
        """
        return self.config_dict.get('test_identifier', str(uuid.uuid1()))

    @property    
    def run_in_serial(self):
        """
        This option can be turned on to force the steps of the shaclAPI to be executed in serial.
        """
        return self.entry_to_bool(self.config_dict.get('run_in_serial', False))
    
    @property
    def reasoning(self):
        """
        This option will turn reasoning in terms of extended output on and off.
        """
        return self.entry_to_bool(self.config_dict.get('reasoning', True))
    
    @property
    def use_pipes(self):
        """
        Whether to use pipes during the multiprocessing. Otherwise, the shaclAPI will use queues.
        """
        return self.entry_to_bool(self.config_dict.get('use_pipes', False))
    
    @property
    def collect_all_validation_results(self):
        """
        Whether to collect all validation results for each mapping. Otherwise, at least one validation result is collected for each given target_shape.  Collecting all results will make the approach blocking.
        """
        return self.entry_to_bool(self.config_dict.get('collect_all_validation_results', False))
    
    @property
    def write_stats(self):
        """
        Whether to write statistics to the output directory.
        """
        return self.entry_to_bool(self.config_dict.get('write_stats', True))

    @property
    def query_extension_per_target_shape(self):
        """
        For each given target shape a query extension can be given. The given query is extended, when merged or replaced with the target definition of the target shape. The query is extended by replacing the last '}' in the query with the extension followed by a '}'.
        """
        return self.config_dict.get('query_extension_per_target_shape', None)
