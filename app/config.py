import json


class Config:
    def __init__(self, config_dict):
        self.config_dict = config_dict
        self.INTERNAL_SPARQL_ENDPOINT = "http://localhost:5000/endpoint"

    @staticmethod
    def from_request_form(request_params):
        config_file_path = request_params.get('config', './quickstart/config.json')
        with open(config_file_path) as config_file:
            final_config = json.load(config_file)
        final_config.update(request_params)
        return Config(final_config)

    def __getitem__(self, name):  # TODO: Remove! Just for convinence
        return eval('self.' + name)

    # ------------------------------- Required Configs -------------------------------------------
    @property
    def config(self):
        '''
        config is the absolute or relativ (with respect to the location of run.py) path to a configuration file.
        --> The Configuration file is json-formated file which can include the same options as the POST - Request.
        --> The Options specified in the POST - Request will override the options in the configuration file.
        '''

        return self.config_dict['config']

    @property
    def query(self):
        '''
        The starshaped query to be executed.
        '''
        return self.config_dict['query']

    @property
    def target_shape(self):
        '''
        The target shape to which the star shaped query refers.
        '''
        return self.config_dict['targetShape']

    @property
    def external_endpoint(self):
        '''
        The external sparql endpoint, which contains the data to be validated.
        '''
        return self.config_dict['external_endpoint']

    @property
    def schema_directory(self):
        '''
        The directory which contains the shape files.
        '''
        return self.config_dict['schemaDir']

    # ------------------------------- Optional Configs -------------------------------------------

    @property
    def save_outputs(self):
        '''
        Whether to save the validation output of the backend to a file.
        '''
        return self.config_dict.get('outputs') or False

    @property
    def output_directory(self):
        '''
        The directory which will be used by the backend to save the validation output of the backend to a file
        '''
        return self.config_dict.get('output_directory') or self.config_dict.get('outputDirectory') or "./output/"

    @property
    def schema_format(self):
        '''
        The format of the shape files. Only JSON is supported.
        '''
        return self.config_dict.get('shape_format') or self.config_dict.get('shapeFormat') or self.config_dict.get('schema_format') or "JSON"

    @property
    def work_in_parallel(self):
        '''
        Whether the backend should work in parallel.
        '''
        return self.config_dict.get('work_in_parallel') or self.config_dict.get('workInParallel') or False

    @property
    def use_selective_queries(self):
        '''
        The travshacl backend can use more selectiv queries. This options is used to turn that on or off.
        '''
        return self.config_dict.get('useSelectiveQueries') or True

    @property
    def max_split_size(self):
        '''
        The max split size.
        '''
        return self.config_dict.get('maxSplit') or 256

    @property
    def order_by_in_queries(self):
        '''
        Whether to use Queries with a ORDER BY Clause.
        '''
        return self.config_dict.get('ORDERBYinQueries') or True

    @property
    def SHACL2SPARQL_order(self):
        '''
        Whether to use the SHACL2SPARQL_order. (TODO: Not used in either case)
        '''
        return self.config_dict.get('SHACL2SPARQLorder') or False

    @property
    def debugging(self):
        '''
        Whether debugging mode is activ. When using debugging mode the api is working as a proxy between the external endpoint and the backend; which allows writing received queries to the standard output.
        '''
        return self.config_dict.get('debugging') or False

    @property
    def backend(self):
        '''
        The backend to use. Only "travshacl" or "s2spy" is implemented.
        '''
        return self.config_dict.get('backend') or "travshacl"

    @property
    def task(self):
        '''
        The task to be done by the backend. (TODO: Only 'a' makes sense here.)
        '''
        return self.config_dict.get('task') or 'a'

    @property
    def traversal_strategie(self):
        '''
        The traversal strategie used by the backend to reduce the shape graph and by the backend to find the execution order. Can be "DFS" or "BFS".
        '''
        return self.config_dict.get('traversalStrategie') or 'DFS'

    @property
    def heuristic(self):
        '''
        Heuristics which the travshacl backend should use.
        '''
        return self.config_dict.get('heuristic') or 'TARGET IN BIG'

    @property
    def replace_target_query(self):
        '''
        Whether or not the api should replace the target query of the target shape.
        '''
        return self.config_dict.get('replace_target_query') or True
    
    @property
    def merge_old_target_query(self):
        '''
        Whether the api should merge the star shaped query with the given target query in the target shape file.
        If this option is inactive the target query of the target shape is basically replaced with the star shaped query.
        '''
        return self.config_dict.get('merge_old_target_query') or True

    @property
    def start_with_target_shape(self):
        '''
        Whether the backend is forced to start the validation process with the target shape.
        '''
        return self.config_dict.get('start_with_target_shape') or True
    
    @property
    def transmission_strategy(self):
        '''
        Which strategy to use to communicate validation results from the backend to the api.
        Can be one of "queue" (Uses multiprocessing.queue), "endpoint" (backend sends validation result via POST to the api) or "" (Results are returned by the backend after the full validation is done --> Only available for the travshacl backend!)
        '''
        return self.config_dict.get('transmission_strategy') or "queue"
    
    @property
    def remove_constraints(self):
        '''
        Whether the api should remove constraints of the target shape not mentioned in the query.
        '''
        return self.config_dict.get('remove_constraints') or False
    
    @property
    def send_initial_query_over_internal_endpoint(self):
        '''
        There might be problems with contactSource and some Sparql Endpoints. These can be fixed by routing through our internal endpoint.
        This will force the api todo so.
        '''
        return self.config_dict.get('send_initial_query_over_internal_endpoint') or False
    
    @property
    def test_output(self):
        '''
        Whether the more simple test output is activated or not.
        '''
        return self.config_dict.get('test_output') or False

# --------------------- Calculated Configs --------------------------------------------------
    @property
    def internal_endpoint(self):
        return self.INTERNAL_SPARQL_ENDPOINT if self.debugging else self.external_endpoint