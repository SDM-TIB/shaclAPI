from app.reduction.travshacl.ReducedShapeParser import ReducedShapeParser
from travshacl.core.ShapeSchema import ShapeSchema
from travshacl.sparql.SPARQLEndpoint import SPARQLEndpoint
from app.reduction.travshacl.ValidationResultStreaming import ValidationResultStreaming
from travshacl.rule_based_validation.Validation import Validation
import app.colors as Colors


class ReducedShapeSchema(ShapeSchema):
    def __init__(self, schema_dir, schema_format, endpoint_url, graph_traversal, heuristics, use_selective_queries, max_split_size, output_dir, order_by_in_queries, save_outputs, work_in_parallel, target_shape, initial_query, replace_target_query, merge_old_target_query, result_transmitter):
        print(Colors.blue(Colors.headline("Shape Parsing and Reduction")))
        self.shapeParser = ReducedShapeParser(initial_query, target_shape, graph_traversal)
        self.shapes = self.shapeParser.parse_shapes_from_dir(
            schema_dir, schema_format, use_selective_queries, max_split_size, order_by_in_queries, replace_target_query=replace_target_query, merge_old_target_query=merge_old_target_query)
        print(Colors.blue(Colors.headline('')))
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

    def validate(self, start_with_target_shape=True):
        """Executes the validation of the shape network."""
        if start_with_target_shape:
            print(Colors.red("Starting with Target Shape"))
            start = [self.targetShape]  # The TargetShape has to be the first Node; because we are limiting the validation to a set of target instances via the star-shape query
        else:
            print(Colors.red("Starting with Shape determined by TravShacl"))
            start = self.get_starting_point()
        print("Starting Point is:" + start[0])
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
    
    def to_json(self):
        print(self.shapeParser.removed_constraints)
        print(self.shapeParser.involvedShapeIDs)


class ReturnShapeSchema(ShapeSchema): # Here the normal ShapeSchema is used and not the reduced one!
    '''
    # Use with:
    # schema = ReturnShapeSchema(
    #    schema_directory, config['shapeFormat'], config['internal_endpoint'], traversal_strategie,
    #    heuristics, config['useSelectiveQueries'], config['maxSplit'], config['outputDirectory'],
    #    config['ORDERBYinQueries'], config['outputs'], config['workInParallel'])
    '''
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