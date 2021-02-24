import re
from validation.ShapeParser import ShapeParser
from validation.core.GraphTraversal import GraphTraversal
from validation.sparql.SPARQLPrefixHandler import getPrefixes
from rdflib.paths import Path
from rdflib import Namespace

class ReducedShapeParser(ShapeParser):
    def __init__(self, query, targetShape):
        super().__init__()
        self.query = query
        self.targetShape = targetShape
        self.currentShape = None
        self.removed_constraints = []

    """
    Normalizes a path in prefixed n3-format ([^]prefix:predicate --> extended_prefix:predicate)
    """
    def _as_path(self, term):
        t_inv = term.startswith('^')
        t_split = term.rfind(':')
        t_namespace = getPrefixes()[term[t_inv:t_split]][1:-1]
        t_path = term[t_split+1:]
        path = Namespace(t_namespace)[t_path]
        #if t_inv:
        #    return ~path
        return path

    """
    Shapes are only relevant, if they (partially) occur in the query. Other shapes can be removed.
    """
    def parseShapesFromDir(self, path, shapeFormat, useSelectiveQueries, maxSplitSize, ORDERBYinQueries, targetDefQuery = None):
        shapes = super().parseShapesFromDir(path, shapeFormat, useSelectiveQueries, maxSplitSize, ORDERBYinQueries)
        involvedShapes = GraphTraversal(GraphTraversal.BFS).traverse_graph(*self.computeReducedEdges(shapes), self.targetShape)
        shapes = [s for s in shapes if s.get_id() in involvedShapes]
        if targetDefQuery:
            for s in shapes:
                if s.get_id() == self.targetShape:
                    s.targetQuery = targetDefQuery
                    s.targetQueryNoPref = targetDefQuery
        return shapes

    """
    parseConstraint can return None, which need to be filtered.
    """
    def parseConstraints(self, array, targetDef, constraintsId):
        self.currentShape = constraintsId[:-3]
        return [c for c in super().parseConstraints(array, targetDef, constraintsId) if c]

    """
    Constraints are only relevant if:
        - subject and object do both NOT belong to the targetShape
        - subject or object belong to the targetShape AND the predicate is part of the query
            (-> inverted paths can be treated equally to normal paths)
    Other constraints are not relevant and result in a None.
    """
    def parseConstraint(self, varGenerator, obj, id, targetDef):
        if self.targetShape == self.currentShape or self.targetShape == obj.get('shape'):
            for t in self.query.get_predicates(replace_prefixes=False):
                path = obj['path'][obj['path'].startswith('^'):]
                if t == path:
                    return super().parseConstraint(varGenerator, obj, id, targetDef)
            self.removed_constraints += [obj.get('path')]
            return None
        return super().parseConstraint(varGenerator, obj, id, targetDef)

    """
    constraints and references are parsed independently based on the json. 
    Constraints that are removed in parseConstraints() should not appear in the references.
    self.removed_constraints keeps track of the removed constraints
    """
    def shapeReferences(self, constraints):
        return {c.get("shape"): c.get("path") for c in constraints\
            if c.get("shape") and c.get("path") not in self.removed_constraints}

    """
    Returns unidirectional dependencies with a single exception: Reversed dependencies are included, if they aim at the targetShape.
    """
    def computeReducedEdges(self, shapes):
        """Computes the edges in the network."""
        dependencies = {s.get_id(): [] for s in shapes}
        reverse_dependencies = {s.get_id(): [] for s in shapes}
        for s in shapes:
            refs = s.getShapeRefs()
            if refs:
                name = s.get_id()
                dependencies[name] = refs
                for ref in refs:
                    if ref == self.targetShape:
                        reverse_dependencies[ref].append(name)
        return dependencies, reverse_dependencies