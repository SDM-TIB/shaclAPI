from shaclapi.reduction.s2spy.ReducedShapeParser import ReducedShapeParser
from s2spy.validation.ShapeNetwork import ShapeNetwork
from s2spy.validation.sparql.SPARQLEndpoint import SPARQLEndpoint
from shaclapi.reduction.s2spy.RuleBasedValidationResultStreaming import RuleBasedValidationResultStreaming
from s2spy.validation.utils import fileManagement
from travshacl.TravSHACL import parse_heuristics
from travshacl.core.GraphTraversal import GraphTraversal
import os, re

import logging
logger = logging.getLogger(__name__)

class ReducedShapeSchema(ShapeNetwork):
    def __init__(self, schema_dir, schema_format, endpoint_url, graph_traversal, heuristics, use_selective_queries, max_split_size, output_dir, order_by_in_queries, save_outputs, work_in_parallel, query, config, result_transmitter):
        self.shaclAPIConfig = config
        self.shapeParser = ReducedShapeParser(query, graph_traversal, config)
        self.shapes, self.node_order, self.target_shape_list = self.shapeParser.parseShapesFromDir(
            schema_dir, schema_format, use_selective_queries, max_split_size, order_by_in_queries, self.shaclAPIConfig)
        self.schema_dir = schema_dir
        self.shapesDict = {shape.getId(): shape for shape in self.shapes}
        self.endpoint = SPARQLEndpoint(endpoint_url)
        self.graphTraversal = graph_traversal
        self.dependencies, self.reverse_dependencies = self.compute_edges()
        self.outputDirName = output_dir
        self.result_transmitter = result_transmitter

    @staticmethod
    def from_config(config, query_object, result_transmitter):
        return ReducedShapeSchema(config.schema_directory, config.schema_format, config.external_endpoint, \
            GraphTraversal[config.traversal_strategy], parse_heuristics(config.heuristic), config.use_selective_queries, \
                config.max_split_size, os.path.join(config.output_directory,config.backend, re.sub('[^\w\-_\. ]', '_', config.test_identifier), ''), config.order_by_in_queries, config.save_outputs, config.work_in_parallel, \
                    query_object, config, result_transmitter)

    def validate(self, start_with_target_shape=True):
        """Executes the validation of the shape network."""
        #logger.debug(f'Target Shapes:{self.target_shape_list}\nNode Order:{self.node_order}\nStart with Target Shape: {start_with_target_shape}\nStart Shape Config: {self.start_shape_for_validation}')

        start = None
        if self.shaclAPIConfig.start_shape_for_validation:
            logger.info("Starting with Shape set in Configuration")
            start = [self.shaclAPIConfig.start_shape_for_validation]
        elif self.node_order != None:
            logger.info("Using Node Order provided by the shaclapi")
            node_order = self.node_order
        elif start_with_target_shape:
            logger.info("Starting with Target Shape")
            start = self.target_shape_list
        else:
            raise NotImplementedError("s2spy has no own logic which could determine a shape to start with. Set one with 'start_shape_for_validation' or set the 'start_with_target_shape' option to true")

        if start != None:
            logger.debug("Starting Point is:" + start[0])
            node_order = self.graphTraversal.traverse_graph(
                self.dependencies, self.reverse_dependencies, start[0])
        
        for s in self.shapes:
            s.computeConstraintQueries()

        RuleBasedValidationResultStreaming(
            self.endpoint,
            node_order,
            self.shapesDict,
            fileManagement.openFile(self.outputDirName, "validation.log"),
            fileManagement.openFile(self.outputDirName, "targets_valid.log"),
            fileManagement.openFile(self.outputDirName, "targets_violated.log"),
            fileManagement.openFile(self.outputDirName, "stats.txt"),
            fileManagement.openFile(self.outputDirName, "traces.csv"),
            self.result_transmitter
        ).exec()
        return {}
    
    def compute_edges(self):
        """Computes the edges in the network."""
        dependencies = {s.getId(): [] for s in self.shapes}
        reverse_dependencies = {s.getId(): [] for s in self.shapes}
        for s in self.shapes:
            refs = s.getShapeRefs()
            if refs:
                name = s.getId()
                dependencies[name] = refs
                for ref in refs:
                    reverse_dependencies[ref].append(name)
        return dependencies, reverse_dependencies