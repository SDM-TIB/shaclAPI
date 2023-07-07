import logging
import os
import re

from TravSHACL.TravSHACL import parse_heuristics
from TravSHACL.core.GraphTraversal import GraphTraversal
from TravSHACL.core.ShapeSchema import ShapeSchema
from TravSHACL.rule_based_validation.Validation import Validation

from shaclapi.reduction.travshacl.ReducedShapeParser import ReducedShapeParser
from shaclapi.reduction.travshacl.ValidationResultStreaming import ValidationResultStreaming

logger = logging.getLogger(__name__)


class ReducedShapeSchema(ShapeSchema):
    def __init__(self, schema_dir, schema_format, endpoint_url, graph_traversal, heuristics,
                 use_selective_queries, max_split_size, output_dir, order_by_in_queries,
                 save_outputs, work_in_parallel, query, config, result_transmitter):
        self.shaclAPIConfig = config
        self.shapeParser = ReducedShapeParser(query, graph_traversal, self.shaclAPIConfig)
        self.shapes, self.node_order, self.target_shape_list = self.shapeParser.parse_shapes_from_dir(
            schema_dir, schema_format, use_selective_queries, max_split_size, order_by_in_queries)
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
        self.result_transmitter = result_transmitter

    @staticmethod
    def from_config(config, query_object, result_transmitter):
        if config.save_outputs:
            output_dir = os.path.join(
                config.output_directory, config.backend, re.sub(r'[^\w\-_.]', '_', config.test_identifier), ''
            )
        else:
            output_dir = None
        return ReducedShapeSchema(
            schema_dir=config.schema_directory,
            schema_format=config.schema_format,
            endpoint_url=config.external_endpoint,
            graph_traversal=GraphTraversal[config.traversal_strategy],
            heuristics=parse_heuristics(config.heuristic),
            use_selective_queries=config.use_selective_queries,
            max_split_size=config.max_split_size,
            output_dir=output_dir,
            order_by_in_queries=config.order_by_in_queries,
            save_outputs=config.save_outputs,
            work_in_parallel=config.work_in_parallel,
            query=query_object,
            config=config,
            result_transmitter=result_transmitter
        )

    def validate(self, start_with_target_shape=True):
        """Executes the validation of the shape network."""
        start = None
        if self.shaclAPIConfig.start_shape_for_validation:
            logger.info('Starting with Shape set in Configuration')
            start = [self.shaclAPIConfig.start_shape_for_validation]
        elif self.node_order is not None:
            logger.info('Using Node Order provided by the shaclapi')
            node_order = self.node_order
        elif start_with_target_shape:
            logger.info('Starting with Target Shape')
            start = self.target_shape_list
        else:
            logger.warning('Starting with Shape determined by Trav-SHACL')
            start = self.get_starting_point()

        if start is not None:
            logger.debug('Starting Point is:' + start[0])
            node_order = self.graphTraversal.traverse_graph(
                self.dependencies, self.reverse_dependencies, start[0])

        for s in self.shapes:
            s.compute_constraint_queries()

        target_shapes = [s for name, s in self.shapesDict.items()
                         if self.shapesDict[name].get_target_query() is not None]
        target_shape_predicates = [s.get_id() for s in target_shapes]
        
        return ValidationResultStreaming(
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


class ReturnShapeSchema(ShapeSchema):  # Here the normal ShapeSchema is used and not the reduced one!
    """
    Example
    -------
    schema = ReturnShapeSchema(
        schema_directory, config['shapeFormat'], config['external_endpoint'], traversal_strategy,
        heuristics, config['useSelectiveQueries'], config['maxSplit'], config['outputDirectory'],
        config['ORDERBYinQueries'], config['outputs'], config['workInParallel'])
    """
    @staticmethod
    def from_config(config):
        return ReturnShapeSchema(
            schema_dir=config.schema_directory,
            schema_format=config.schema_format,
            endpoint=config.external_endpoint,
            graph_traversal=GraphTraversal[config.traversal_strategy],
            heuristics=parse_heuristics(config.heuristic),
            use_selective_queries=config.use_selective_queries,
            max_split_size=config.max_split_size,
            output_dir=config.output_directory,
            order_by_in_queries=config.order_by_in_queries,
            save_outputs=config.save_outputs,
            work_in_parallel=config.work_in_parallel
        )

    def validate(self):
        """Executes the validation of the shape network."""
        start = self.get_starting_point()
        node_order = self.graphTraversal.traverse_graph(self.dependencies, self.reverse_dependencies, start[0])  # TODO: deal with more than one possible starting point

        for s in self.shapes:
            s.compute_constraint_queries()

        target_shapes = [s for name, s in self.shapesDict.items()
                         if self.shapesDict[name].get_target_query() is not None]
        target_shape_predicates = [s.get_id() for s in target_shapes]

        return Validation(
            self.endpoint,
            node_order,
            self.shapesDict,
            target_shape_predicates,
            self.selectivityEnabled,
            self.outputDirName,
            self.saveStats,
            self.saveTargetsToFile
        ).exec()
