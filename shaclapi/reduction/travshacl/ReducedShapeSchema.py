from shaclapi.reduction.travshacl.ReducedShapeParser import ReducedShapeParser
from travshacl.core.ShapeSchema import ShapeSchema
from shaclapi.reduction.travshacl.ValidationResultStreaming import ValidationResultStreaming
from travshacl.rule_based_validation.Validation import Validation
from travshacl.TravSHACL import parse_heuristics
from travshacl.core.GraphTraversal import GraphTraversal
import os, re

import logging
logger = logging.getLogger(__name__)

class ReducedShapeSchema(ShapeSchema):
    def __init__(self, schema_dir, schema_format, endpoint_url, graph_traversal, heuristics, use_selective_queries, max_split_size, output_dir, order_by_in_queries, save_outputs, work_in_parallel, target_shape, initial_query, replace_target_query, merge_old_target_query, remove_constraints, prune_shape_network, start_shape_for_validation, result_transmitter):
        self.shapeParser = ReducedShapeParser(initial_query, target_shape, graph_traversal, remove_constraints)
        self.shapes, self.node_order = self.shapeParser.parse_shapes_from_dir(
            schema_dir, schema_format, use_selective_queries, max_split_size, order_by_in_queries, replace_target_query=replace_target_query, merge_old_target_query=merge_old_target_query, prune_shape_network=prune_shape_network)
        self.schema_dir = schema_dir
        self.shapesDict = {shape.get_id(): shape for shape in self.shapes}
        self.endpointURL = endpoint_url
        self.graphTraversal = graph_traversal
        self.parallel = work_in_parallel
        self.dependencies, self.reverse_dependencies = self.compute_edges()
        self.compute_in_and_outdegree()
        self.heuristics = heuristics
        self.outputDirName = output_dir
        self.selectivityEnabled = use_selective_queries
        self.saveStats = output_dir is not None
        self.saveTargetsToFile = save_outputs
        self.targetShape = target_shape
        self.result_transmitter = result_transmitter
        self.start_shape_for_validation = start_shape_for_validation
    
    @staticmethod
    def from_config(config, query_object, result_transmitter):
        return ReducedShapeSchema(config.schema_directory, config.schema_format, config.external_endpoint, \
            GraphTraversal[config.traversal_strategy], parse_heuristics(config.heuristic), config.use_selective_queries, \
                config.max_split_size, os.path.join(config.output_directory,config.backend, re.sub('[^\w\-_\. ]', '_', config.test_identifier), ''), config.order_by_in_queries, config.save_outputs, config.work_in_parallel, \
                    config.target_shape, query_object, config.replace_target_query, config.merge_old_target_query,config.remove_constraints, config.prune_shape_network, config.start_shape_for_validation, result_transmitter)

    def validate(self, start_with_target_shape=True):
        """Executes the validation of the shape network."""
        if start_with_target_shape:
            logger.info("Starting with Target Shape")
            node_order = self.node_order
        else:
            if self.start_shape_for_validation:
                logger.warn("Starting with Shape set in Configuration")
                start = [self.start_shape_for_validation]
            else:
                logger.warn("Starting with Shape determined by TravShacl")
                start = self.get_starting_point()
                logger.debug("Starting Point is:" + start[0])
                # TODO: deal with more than one possible starting point
                node_order = self.graphTraversal.traverse_graph(
                    self.dependencies, self.reverse_dependencies, start[0])

        for s in self.shapes:
            s.compute_constraint_queries()

        target_shapes = [s for name, s in self.shapesDict.items()
                         if self.shapesDict[name].get_target_query() is not None]
        target_shape_predicates = [s.get_id() for s in target_shapes]
        
        result = ValidationResultStreaming(
            self.endpointURL,
            node_order,
            self.shapesDict,
            target_shape_predicates,
            self.selectivityEnabled,
            self.outputDirName,
            self.saveStats,
            self.saveTargetsToFile,
            self.result_transmitter
        ).exec()
        return result
    


class ReturnShapeSchema(ShapeSchema): # Here the normal ShapeSchema is used and not the reduced one!
    '''
    # Use with:
    # schema = ReturnShapeSchema(
    #    schema_directory, config['shapeFormat'], config['external_endpoint'], traversal_strategie,
    #    heuristics, config['useSelectiveQueries'], config['maxSplit'], config['outputDirectory'],
    #    config['ORDERBYinQueries'], config['outputs'], config['workInParallel'])
    '''
    @staticmethod
    def from_config(config):
        return ReturnShapeSchema(config.schema_directory, config.schema_format, config.external_endpoint, GraphTraversal[config.traversal_strategy], parse_heuristics(config.heuristic), config.use_selective_queries, config.max_split_size, config.output_directory, config.order_by_in_queries, config.save_outputs, config.work_in_parallel)

    def validate(self):
        """Executes the validation of the shape network."""
        start = self.get_starting_point()
        node_order = self.graphTraversal.traverse_graph(self.dependencies, self.reverse_dependencies, start[0])  # TODO: deal with more than one possible starting point

        for s in self.shapes:
            s.compute_constraint_queries()

        target_shapes = [s for name, s in self.shapesDict.items()
                         if self.shapesDict[name].get_target_query() is not None]
        target_shape_predicates = [s.get_id() for s in target_shapes]

        result = Validation(
            self.endpointURL,
            node_order,
            self.shapesDict,
            target_shape_predicates,
            self.selectivityEnabled,
            self.outputDirName,
            self.saveStats,
            self.saveTargetsToFile
        ).exec()
        return result