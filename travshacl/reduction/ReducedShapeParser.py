import re
from validation.ShapeParser import ShapeParser
from validation.core.GraphTraversal import GraphTraversal

class ReducedShapeParser(ShapeParser):
	def __init__(self, query, targetShape):
		super().__init__()
		self.query = query
		self.targetShape = targetShape
		self.currentShape = None

	def parseShapesFromDir(self, path, shapeFormat, useSelectiveQueries, maxSplitSize, ORDERBYinQueries):
		shapes = super().parseShapesFromDir(path, shapeFormat, useSelectiveQueries, maxSplitSize, ORDERBYinQueries)
		involvedShapes = GraphTraversal(GraphTraversal.BFS).traverse_graph(*self.computeReducedEdges(shapes), self.targetShape)
		shapes = [s for s in shapes if s.getId() in involvedShapes]
		return shapes

	def parseConstraints(self, array, targetDef, constraintsId):
		self.currentShape = constraintsId[:-3]
		return [c for c in super().parseConstraints(array, targetDef, constraintsId) if c]

	def parseConstraint(self, varGenerator, obj, id, targetDef):
		if self.targetShape == self.currentShape:
			path_ind = obj.get('path').rfind(':')+1
			path_name = obj.get('path')[path_ind:]	#Remove prefixes, paths are considered as unique!!!
			if not [t for t in self.query.triples if t.predicat.endswith(path_name)]:
				return None
		elif obj.get('shape') == self.targetShape:
			path_ind = obj.get('path').rfind(':')+1
			path_name = obj.get('path')[path_ind:]	#Remove prefixes, paths are considered as unique!!!
			if not [t for t in self.query.triples if t.predicat.endswith(path_name)]:
				return None
		return super().parseConstraint(varGenerator, obj, id, targetDef)

	def shapeReferences(self, constraints):
		references = {}
		for c in constraints:
			path = c.get("path")
			shape = c.get("shape")
			if shape:
				#Reference from or to targetShape
				if shape == self.targetShape or self.currentShape == self.targetShape:
					path_ind = path.rfind(':')+1
					path_name = path[path_ind:]	#Remove prefixes, paths are considered as unique!!!
					if [t for t in self.query.triples if t.predicat.endswith(path_name)]:
						references[shape] = path
				else:
					references[shape] = path
		return references

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