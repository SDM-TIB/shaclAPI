from reduction.ReducedShapeParser import ReducedShapeParser
from validation.ShapeNetwork import ShapeNetwork
from validation.sparql.SPARQLEndpoint import SPARQLEndpoint

class ReducedShapeNetwork(ShapeNetwork):
	def __init__(self, schemaDir, schemaFormat, endpointURL, graphTraversal, validationTask, heuristics,
				 useSelectiveQueries, maxSplitSize, outputDir, ORDERBYinQueries, SHACL2SPARQLorder, query, targetShape, workInParallel=False, targetDefQuery = None):
		self.shapes = ReducedShapeParser(query, targetShape).parseShapesFromDir(schemaDir, schemaFormat,
														useSelectiveQueries, maxSplitSize, ORDERBYinQueries, targetDefQuery = targetDefQuery)
		print([s.getTargetQuery() for s in  self.shapes])
		self.shapesDict = {shape.getId(): shape for shape in self.shapes}
		self.endpointURL = endpointURL
		self.endpoint = SPARQLEndpoint(endpointURL)  # used in old_approach
		self.graphTraversal = graphTraversal
		self.validationTask = validationTask
		self.parallel = workInParallel
		self.dependencies, self.reverse_dependencies = self.computeEdges()
		self.computeInAndOutDegree()
		self.heuristics = heuristics
		self.outputDirName = outputDir
		self.selectivityEnabled = useSelectiveQueries
		self.useSHACL2SPARQLORDER = SHACL2SPARQLorder