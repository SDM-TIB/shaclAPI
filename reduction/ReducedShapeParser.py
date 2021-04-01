import re
from travshacl.core.ShapeParser import ShapeParser
from travshacl.core.GraphTraversal import GraphTraversal
from travshacl.sparql.SPARQLPrefixHandler import get_prefixes, get_prefix_string
from rdflib.paths import Path
from rdflib import Namespace
from app.query import Query
import app.colors as Colors


class ReducedShapeParser(ShapeParser):
    def __init__(self, query, targetShape):
        super().__init__()
        self.query = query
        self.targetShape = targetShape
        self.currentShape = None
        self.removed_constraints = {}
        self.involvedShapeIDs = []

    """
    Shapes are only relevant, if they (partially) occur in the query. Other shapes can be removed.
    """

    def parse_shapes_from_dir(self, path, shapeFormat, useSelectiveQueries, maxSplitSize, ORDERBYinQueries):
        shapes = super().parse_shapes_from_dir(path, shapeFormat,
                                               useSelectiveQueries, maxSplitSize, ORDERBYinQueries)
        self.involvedShapeIDs = GraphTraversal(GraphTraversal.BFS).traverse_graph(
            *self.computeReducedEdges(shapes), self.targetShape)
        
        print("Involved Shapes:", Colors.grey(str(self.involvedShapeIDs)), sep='\n')
        print("Removed Constraints:", Colors.grey(str(self.removed_constraints)), sep='\n')
        shapes = [s for s in shapes if s.get_id() in self.involvedShapeIDs]

        # Replacing old targetQuery with new one
        for s in shapes:
            if s.get_id() == self.targetShape:
                # The Shape already has a target query
                print("Starshaped Query:", Colors.grey(
                    self.query.query_string), sep='\n')
                if s.targetQuery:
                    print("Old TargetDef:", Colors.grey(
                        s.targetQueryNoPref), sep='\n')
                    oldTargetQuery = Query(s.targetQuery)
                    targetQuery = self.query.merge_as_target_query(
                        oldTargetQuery)
                else:
                    targetQuery = self.query.as_target_query()
                s.targetQuery = get_prefix_string() + targetQuery
                s.targetQueryNoPref = targetQuery
                print("New TargetDef:", Colors.grey(targetQuery), sep='\n')
        return shapes

    """
    parseConstraint can return None, which need to be filtered.
    """

    def parse_constraints(self, array, targetDef, constraintsId):
        self.currentShape = constraintsId[:-3]
        self.removed_constraints[self.currentShape] = []
        return [c for c in super().parse_constraints(array, targetDef, constraintsId) if c]

    """
    Constraints are only relevant if:
        - subject and object do both NOT belong to the targetShape
        OR
        - subject or object belong to the targetShape AND the predicate is part of the query
            (-> inverted paths can be treated equally to normal paths)
    Other constraints are not relevant and result in a None.
    """

    def parse_constraint(self, varGenerator, obj, id, targetDef):
        if self.targetShape == self.currentShape or self.targetShape == obj.get('shape'):
            path = obj['path'][obj['path'].startswith('^'):]
            if path in self.query.get_predicates(replace_prefixes=False):
                return super().parse_constraint(varGenerator, obj, id, targetDef)
            else:
                self.removed_constraints[self.currentShape] += [obj.get('path')]
                return None
        return super().parse_constraint(varGenerator, obj, id, targetDef)

    """
    constraints and references are parsed independently based on the json. 
    Constraints that are removed in parse_constraint() should not appear in the references.
    self.removed_constraints keeps track of the removed constraints
    """

    def shape_references(self, constraints):
        return {c.get("shape"): c.get("path") for c in constraints
                if c.get("shape") and c.get("path") not in self.removed_constraints[self.currentShape]}

    """
    Returns unidirectional dependencies with a single exception: Reversed dependencies are included, if they aim at the targetShape.
    """

    def computeReducedEdges(self, shapes):
        """Computes the edges in the network."""
        dependencies = {s.get_id(): [] for s in shapes}
        reverse_dependencies = {s.get_id(): [] for s in shapes}
        for s in shapes:
            refs = s.get_shape_refs()
            if refs:
                name = s.get_id()
                dependencies[name] = refs
                for ref in refs:
                    if ref == self.targetShape:
                        reverse_dependencies[ref].append(name)
        return dependencies, reverse_dependencies
