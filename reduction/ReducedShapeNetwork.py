from reduction.ReducedShapeParser import ReducedShapeParser
from validation.ShapeNetwork import ShapeNetwork
from validation.sparql.SPARQLEndpoint import SPARQLEndpoint
from validation.rule_based_validation.Validation import Validation


class ReducedShapeNetwork(ShapeNetwork):
    def __init__(self, schemaDir, schemaFormat, endpointURL, graphTraversal, validationTask, heuristics, useSelectiveQueries, maxSplitSize, outputDir, ORDERBYinQueries, SHACL2SPARQLorder, query, targetShape,  saveOutputs, workInParallel=False, targetDefQuery=None):
        self.shapes = ReducedShapeParser(query, targetShape).parseShapesFromDir(
            schemaDir, schemaFormat, useSelectiveQueries, maxSplitSize, ORDERBYinQueries, targetDefQuery=targetDefQuery)
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
        self.saveStats = outputDir is not None
        self.saveTargetsToFile = saveOutputs
    

    def getInstances(self, node_order, option):
        """
        Reports valid and violated constraints of the graph
        :param node_order:
        :param option: has three possible values: 'all', 'valid', 'violated'
        """
        targetShapes = [s for name, s in self.shapesDict.items()
                        if self.shapesDict[name].getTargetQuery() is not None]
        targetShapePredicates = [s.getId() for s in targetShapes]

        result = Validation(
            self.endpointURL,
            node_order,
            self.shapesDict,
            option,
            targetShapePredicates,
            self.selectivityEnabled,
            self.useSHACL2SPARQLORDER,
            self.outputDirName,
            self.saveStats,
            self.saveTargetsToFile
        ).exec()
        return result
