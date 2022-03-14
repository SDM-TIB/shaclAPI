import logging
from shaclapi.query import Query
from functools import reduce

logger = logging.getLogger(__name__)

class Reduction:
    def __init__(self,parser):
        self.parser = parser
        self.involvedShapesPerTarget = {}

    def reduce_shape_network(self, shapes, target_shape_ids):
        involvedShapes = set()
        for target_shape in target_shape_ids:
            shapeIds = list(self.parser.graph_traversal.traverse_graph(
                *self.parser.computeReducedEdges(shapes), target_shape))
            self.involvedShapesPerTarget[target_shape] = shapeIds
            involvedShapes = involvedShapes.union(shapeIds)
        logger.debug("Involved Shapes:" + str(self.involvedShapesPerTarget))
        shapes = [s for s in shapes if self.parser.shape_get_id(s) in involvedShapes]
        return shapes
    
    def replace_target_query(self, shapes, query, target_shape_ids, merge_old_target_query):
        logger.info("Using Shape Schema WITH replaced target query!")
        for s in shapes:
            s_id = self.parser.shape_get_id(s)
            if s_id in target_shape_ids:
                # If there isn't a shape based on the target shape, reduce the target definition
                if len(target_shape_ids) == 1 or s_id not in reduce(lambda a,b: a+b, [self.involvedShapesPerTarget[targetShape] for targetShape in target_shape_ids if targetShape != s_id]):
                    # The Shape already has a target query
                    logger.debug("Starshaped Query:\n" + query.query_string)
                    if s.targetQuery and merge_old_target_query:
                        logger.debug("Old TargetDef: \n" + s.targetQuery)
                        oldTargetQuery = Query(s.targetQuery)
                        targetQuery = query.merge_as_target_query(
                            oldTargetQuery)
                    else:
                        if not '?x' in query.query_string:
                            new_query_string = query.query_string.replace(query.target_var, '?x')
                            targetQuery = Query(new_query_string).as_target_query()
                        else:
                            targetQuery = query.query_string
                    self.parser.replace_target_query(s, targetQuery)
                    logger.debug("New TargetDef:\n" + targetQuery)
    
    def node_order(self, target_shape_ids):
        node_order = target_shape_ids
        for target_shape in target_shape_ids:
            node_order = node_order + list(self.involvedShapesPerTarget[target_shape])
        
        unique_node_order = []
        unique_nodes = set()
        for node in node_order:
            if node not in unique_nodes:
                unique_node_order.append(node)
                unique_nodes.add(node)
        logger.debug('Node Order estimated by the shaclapi: ' + str(unique_node_order))
        return unique_node_order
        

