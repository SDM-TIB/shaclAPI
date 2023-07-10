import logging
import re
from functools import reduce

from SHACL2SPARQLpy.ShapeParser import ShapeParser

from shaclapi.reduction.Reduction import Reduction

logger = logging.getLogger(__name__)
re_https = re.compile("https?://")


# Note the internal structure of ShapeParser:
# parse_shapes_from_dir --> calls for each shape: parse_constraints (--> parse_constraint), shape_references; Afterwards we call computeReducedEdges to find the involvedShapeIDs.
class ReducedShapeParser(ShapeParser):
    def __init__(self, query, graph_traversal, config):
        super().__init__()
        self.query = query
        self.targetShapes = config.target_shape if isinstance(config.target_shape, dict) else {'UNDEF': [config.target_shape]}
        self.targetShapeList = [shape for shape in reduce(lambda a, b: a + b, self.targetShapes.values()) if shape is not None]
        self.currentShape = None
        self.removed_constraints = {}
        self.involvedShapeIDs = []
        self.graph_traversal = graph_traversal
        self.config = config

    def parseShapesFromDir(self, path, shapeFormat, useSelectiveQueries, maxSplitSize, ORDERBYinQueries):
        """
        Parses shapes from a directory. However, shapes are only relevant if they occur in the query or are
        reachable from shapes occurring in the query. The remaining shapes can be removed.
        """
        all_shapes = super().parseShapesFromDir(path, shapeFormat, useSelectiveQueries, maxSplitSize, ORDERBYinQueries)
        reducer = Reduction(self)

        # Step 1: Prune not reachable shapes
        reduced_shapes = reducer.reduce_shape_network(all_shapes, self.targetShapeList)
        if self.config.prune_shape_network:
            shapes = reduced_shapes
        else:
            shapes = all_shapes
            logger.warning('Shape Network is not pruned!')

        logger.debug('Removed Constraints:' + str(self.removed_constraints))

        # Step 2: Replace appropriate target queries
        if self.query is not None and self.config.replace_target_query and 'UNDEF' not in self.targetShapes:
            reducer.replace_target_query(shapes, self.query, self.targetShapes, self.targetShapeList, self.config.merge_old_target_query, self.config.query_extension_per_target_shape)
        else:
            logger.warning('Using Shape Schema WITHOUT replaced target query!')
        
        if self.config.start_with_target_shape:
            return shapes, reducer.node_order(self.targetShapeList), self.targetShapeList
        else:
            return shapes, None, self.targetShapeList

    def replace_target_query(self, shape, query):
        shape.targetQuery = shape.prefix_string + query
    
    def shape_get_id(self, shape):
        return shape.getId()

    def parseConstraints(self, shapeName, array, targetDef, constraintsId):
        self.currentShape = constraintsId[:-3]
        self.removed_constraints[self.currentShape] = []
        return [c for c in super().parseConstraints(shapeName, array, targetDef, constraintsId) if c]

    def parse_constraints_ttl(self, array, target_def, constraints_id):
        self.currentShape = '<' + constraints_id[:-3] + '>'
        self.removed_constraints[self.currentShape] = []
        return [c for c in super().parse_constraints_ttl(array, target_def, constraints_id) if c]

    def parseConstraint(self, varGenerator, obj, id, targetDef):
        """
        Constraints are only relevant if:
            - subject and object do both NOT belong to the targetShape OR
            - subject or object belong to the targetShape AND the predicate is part of the query
              (-> inverted paths can be treated equally to normal paths)

        Other constraints are not relevant and result in an empty list.
        """
        if self.query is not None and self.config.remove_constraints and (self.currentShape in self.targetShapeList or obj.get('shape') in self.targetShapeList):
            path = obj['path'][obj['path'].startswith('^'):]
            if re_https.match(path):
                path = '<' + path + '>'
                query_predicates = self.query.get_predicates(replace_prefixes=True)
            else:
                query_predicates = self.query.get_predicates(replace_prefixes=False)
            if path in query_predicates:
                return super().parseConstraint(varGenerator, obj, id, targetDef)
            else:
                self.removed_constraints[self.currentShape] += [obj.get('path')]
                return []
        return super().parseConstraint(varGenerator, obj, id, targetDef)

    def shapeReferences(self, constraints):
        """
        Constraints and references are parsed independently based on the input SHACL shape schema.
        Constraints that are removed in parse_constraint() should not appear in the references.
        self.removed_constraints keeps track of the removed constraints

        shape_references is used to get the references in self.currentShape to other shapes.
        It then returns ONE path of a constraint referencing to that shape (The other ones are ignored?!)
        """
        return {c.get('shape'): c.get('path') for c in constraints
                if c.get('shape') and c.get('path') not in self.removed_constraints[self.currentShape]}

    def computeReducedEdges(self, shapes):
        """
        Computes the edges in the network.

        Returns unidirectional dependencies of the shapes in the network.
        """
        dependencies = {s.getId(): [] for s in shapes}
        reverse_dependencies = {s.getId(): [] for s in shapes}
        for s in shapes:
            refs = s.getShapeRefs()
            if refs:
                name = s.getId()
                dependencies[name] = refs
        return dependencies, reverse_dependencies
