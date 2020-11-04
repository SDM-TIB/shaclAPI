import re
from validation.ShapeParser import ShapeParser
from validation.core.GraphTraversal import GraphTraversal

class ReducedShapeParser(ShapeParser):
	def __init__(self, query, targetShape):
		super().__init__()
		self.query = self.parseQuery(query, targetShape)
		self.targetShape = targetShape
		self.currentShape = None

	def parseShapesFromDir(self, path, shapeFormat, useSelectiveQueries, maxSplitSize, ORDERBYinQueries):
		shapes = super().parseShapesFromDir(path, shapeFormat, useSelectiveQueries, maxSplitSize, ORDERBYinQueries)
		involvedShapes = GraphTraversal(GraphTraversal.BFS).traverse_graph(*self.computeReducedEdges(shapes), self.targetShape)
		return [s for s in shapes if s.getId() in involvedShapes]

	def parseQuery(self, query, targetShape):
		query_rep = []
		targetVar = re.findall(r"SELECT (\?[^[]) WHERE", query)[0]
		#Starting with { select everything until last . and ending with }
		where = re.findall(r"\{([^[]*.)[^[]*\}", query)[0]
		#Select everything from \n or \t until . and split it on ' '
		triples = re.findall(r"([^ \t\n]+) ([^ ]+) ([^.\n\}]+)", where)
		for s, p, o in triples:
			if s == targetVar:
				if p.startswith('^'):
					constraint = {
						'path': p[1:],
						'shape': targetShape,
					}
					query_rep.append(constraint)
				constraint = {
					'path': p
				}
				query_rep.append(constraint)
		return query_rep

	def parseConstraints(self, array, targetDef, constraintsId):
		self.currentShape = constraintsId[:-3]
		return [c for c in super().parseConstraints(array, targetDef, constraintsId) if c]

	def parseConstraint(self, varGenerator, obj, id, targetDef):
		if self.targetShape == self.currentShape:
			if not len([p for p in self.query if p['path'] == obj.get('path')]):
				return None
		elif obj.get('shape') == self.targetShape:
			if not len([p for p in self.query if p['path'] == obj.get('path')]):
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
					if 0 < len([p for p in self.query if p['path'] == path]):
						references[shape] = path
			elif shape:
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