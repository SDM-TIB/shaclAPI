import re, sys
from s2spy.validation.ShapeParser import ShapeParser
sys.path.append('./s2spy/validation')
import validation.sparql.SPARQLPrefixHandler as SPARQLPrefixHandler
sys.path.remove('./s2spy/validation')
from rdflib.paths import Path
from rdflib import Namespace
from app.query import Query
import app.colors as Colors

# Note the internal structure of ShapeParser:
# parse_shapes_from_dir --> calls for each shape: parse_constraints (--> parse_constraint), shape_references; Afterwards we call computeReducedEdges to find the involvedShapeIDs.
class ReducedShapeParser(ShapeParser):
    def __init__(self, query, targetShape, graph_traversal):
        super().__init__()
        self.query = query
        self.targetShape = targetShape
        self.currentShape = None
        self.removed_constraints = {}
        self.involvedShapeIDs = []
        self.graph_traversal = graph_traversal

    """
    Shapes are only relevant, if they (partially) occur in the query. Other shapes can be removed.
    """

    def parseShapesFromDir(self, path, shapeFormat, useSelectiveQueries, maxSplitSize, ORDERBYinQueries, replace_target_query=True, merge_old_target_query=True):
        shapes = super().parseShapesFromDir(path, shapeFormat,
                                               useSelectiveQueries, maxSplitSize, ORDERBYinQueries)
        self.involvedShapeIDs = self.graph_traversal.traverse_graph(
            *self.computeReducedEdges(shapes), self.targetShape)
        
        print("Involved Shapes:", Colors.grey(str(self.involvedShapeIDs)), sep='\n')
        print("Removed Constraints:", Colors.grey(str(self.removed_constraints)), sep='\n')
        shapes = [s for s in shapes if s.getId() in self.involvedShapeIDs]

        # Replacing old targetQuery with new one
        if replace_target_query:
            print(Colors.red("Using Shape Schema WITH replaced target query!"))
            for s in shapes:
                if s.getId() == self.targetShape:
                    # The Shape already has a target query
                    print("Starshaped Query:", Colors.grey(
                        self.query.query_string), sep='\n')
                    if s.targetQuery and merge_old_target_query:
                        print("Old TargetDef:", Colors.grey(
                            s.targetQuery), sep='\n')
                        oldTargetQuery = Query(s.targetQuery)
                        targetQuery = self.query.merge_as_target_query(
                            oldTargetQuery)
                    else:
                        if not '?x' in self.query.query_string:
                            new_query_string = self.query.as_valid_query().replace(self.query.target_var, '?x')
                            targetQuery = Query(new_query_string).as_target_query()
                        else:
                            targetQuery = self.query.query_string
                    s.targetQuery = SPARQLPrefixHandler.getPrefixString() + targetQuery
                    print("New TargetDef:", Colors.grey(targetQuery), sep='\n')
        else:
            print(Colors.red("Using Shape Schema WITHOUT replaced target query!"))
        return shapes

    """
    parseConstraint can return None, which need to be filtered.
    """
    def parseConstraints(self,shapeName, array, targetDef, constraintsId):
        self.currentShape = constraintsId[:-3]
        self.removed_constraints[self.currentShape] = []
        return [c for c in super().parseConstraints(shapeName, array, targetDef, constraintsId) if c]

    """
    Constraints are only relevant if:
        - subject and object do both NOT belong to the targetShape
        OR
        - subject or object belong to the targetShape AND the predicate is part of the query
            (-> inverted paths can be treated equally to normal paths)
    Other constraints are not relevant and result in a None.
    """

    def parseConstraint(self, varGenerator, obj, id, targetDef):
        if self.targetShape == self.currentShape or self.targetShape == obj.get('shape'):
            path = obj['path'][obj['path'].startswith('^'):]
            if path in self.query.get_predicates(replace_prefixes=False):
                return super().parseConstraint(varGenerator, obj, id, targetDef)
            else:
                self.removed_constraints[self.currentShape] += [obj.get('path')]
                return None
        return super().parseConstraint(varGenerator, obj, id, targetDef)

    """
    constraints and references are parsed independently based on the json. 
    Constraints that are removed in parse_constraint() should not appear in the references.
    self.removed_constraints keeps track of the removed constraints
    """

    def shapeReferences(self, constraints):
        return {c.get("shape"): c.get("path") for c in constraints
                if c.get("shape") and c.get("path") not in self.removed_constraints[self.currentShape]}

    """
    Returns unidirectional dependencies with a single exception: Reversed dependencies are included, if they aim at the targetShape.
    """

    def computeReducedEdges(self, shapes):
        """Computes the edges in the network."""
        dependencies = {s.getId(): [] for s in shapes}
        reverse_dependencies = {s.getId(): [] for s in shapes}
        for s in shapes:
            refs = s.getShapeRefs()
            if refs:
                name = s.getId()
                dependencies[name] = refs
                for ref in refs:
                    if ref == self.targetShape:
                        reverse_dependencies[ref].append(name)
        return dependencies, reverse_dependencies
