from app.reduction.s2spy.ReducedShapeParser import ReducedShapeParser
from s2spy.validation.ShapeNetwork import ShapeNetwork
from s2spy.validation.sparql.SPARQLEndpoint import SPARQLEndpoint
from app.reduction.s2spy.RuleBasedValidationResultStreaming import RuleBasedValidationResultStreaming
from s2spy.validation.utils import fileManagement
from travshacl.TravSHACL import parse_heuristics
from travshacl.core.GraphTraversal import GraphTraversal
import app.colors as Colors


class ReducedShapeSchema(ShapeNetwork):
    def __init__(self, schema_dir, schema_format, endpoint_url, graph_traversal, heuristics, use_selective_queries, max_split_size, output_dir, order_by_in_queries, save_outputs, work_in_parallel, target_shape, initial_query, replace_target_query, merge_old_target_query, remove_constraints, prune_shape_network, start_shape_for_validation, result_transmitter):
        print(Colors.blue(Colors.headline("Shape Parsing and Reduction")))
        self.shapeParser = ReducedShapeParser(initial_query, target_shape, graph_traversal, remove_constraints)
        self.shapes = self.shapeParser.parseShapesFromDir(
            schema_dir, schema_format, use_selective_queries, max_split_size, order_by_in_queries, replace_target_query=replace_target_query, merge_old_target_query=merge_old_target_query, prune_shape_network=prune_shape_network)
        print(Colors.blue(Colors.headline('')))
        self.schema_dir = schema_dir
        self.shapesDict = {shape.getId(): shape for shape in self.shapes}
        self.endpoint = SPARQLEndpoint(endpoint_url)
        self.graphTraversal = graph_traversal
        self.dependencies, self.reverse_dependencies = self.compute_edges()
        self.outputDirName = output_dir
        self.targetShape = target_shape
        self.result_transmitter = result_transmitter
        self.start_shape_for_validation = start_shape_for_validation

    @staticmethod
    def from_config(config, query_object, result_transmitter):
        return ReducedShapeSchema(config.schema_directory, config.schema_format, config.internal_endpoint, \
            GraphTraversal[config.traversal_strategie], parse_heuristics(config.heuristic), config.use_selective_queries, \
                config.max_split_size, config.output_directory, config.order_by_in_queries, config.save_outputs, config.work_in_parallel, \
                    config.target_shape, query_object, config.replace_target_query, config.merge_old_target_query, config.remove_constraints, config.prune_shape_network, config.start_shape_for_validation, result_transmitter)

    def validate(self, start_with_target_shape=True):
        """Executes the validation of the shape network."""
        if start_with_target_shape:
            print(Colors.red("Starting with Target Shape"))
            start = [self.targetShape]  # The TargetShape has to be the first Node; because we are limiting the validation to a set of target instances via the star-shape query
        else:
            if self.start_shape_for_validation:
                print(Colors.red("Starting with Shape set in Configuration"))
                start = [self.start_shape_for_validation]
            else:
                raise NotImplementedError
        print("Starting Point is:" + start[0])
        # TODO: deal with more than one possible starting point
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
    
    def to_json(self):
        print(self.shapeParser.removed_constraints)
        print(self.shapeParser.involvedShapeIDs)

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