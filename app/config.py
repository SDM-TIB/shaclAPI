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
        return self.config_dict['config']

    @property
    def query(self):
        return self.config_dict['query']

    @property
    def target_shape(self):
        return self.config_dict['targetShape']

    @property
    def external_endpoint(self):
        return self.config_dict['external_endpoint']

    @property
    def schema_directory(self):
        return self.config_dict['schemaDir']

    # ------------------------------- Optional Configs -------------------------------------------
    @property
    def output_directory(self):
        return self.config_dict.get('output_directory') or self.config_dict.get('outputDirectory') or "./output/"

    @property
    def schema_format(self):
        return self.config_dict.get('shape_format') or self.config_dict.get('shapeFormat') or self.config_dict.get('schema_format') or "JSON"

    @property
    def work_in_parallel(self):
        return self.config_dict.get('work_in_parallel') or self.config_dict.get('workInParallel') or False

    @property
    def use_selective_queries(self):
        return self.config_dict.get('useSelectiveQueries') or True

    @property
    def max_split_size(self):
        return self.config_dict.get('maxSplit') or 256

    @property
    def order_by_in_queries(self):
        return self.config_dict.get('ORDERBYinQueries') or True

    @property
    def SHACL2SPARQL_order(self):
        return self.config_dict.get('SHACL2SPARQLorder') or False

    @property
    def debugging(self):
        return self.config_dict.get('debugging') or False

    @property
    def save_outputs(self):
        return self.config_dict.get('outputs') or False

    @property
    def backend(self):
        return self.config_dict.get('backend') or "travshacl"

    @property
    def task(self):
        return self.config_dict.get('task') or 'a'

    @property
    def traversal_strategie(self):
        return self.config_dict.get('traversalStrategie') or 'DFS'

    @property
    def heuristic(self):
        return self.config_dict.get('heuristic') or 'TARGET IN BIG'

    @property
    def internal_endpoint(self):
        return self.INTERNAL_SPARQL_ENDPOINT if self.debugging else self.external_endpoint

    @property
    def replace_target_query(self):
        return self.config_dict.get('replace_target_query') or True
    
    @property
    def merge_old_target_query(self):
        return self.config_dict.get('merge_old_target_query') or True

    @property
    def start_with_target_shape(self):
        return self.config_dict.get('start_with_target_shape') or True
    
    @property
    def transmission_strategy(self):
        return self.config_dict.get('transmission_strategy') or "queue"
    
    @property
    def remove_constraints(self):
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
        return self.config_dict.get('test_output') or False