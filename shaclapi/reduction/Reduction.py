import logging
from functools import reduce

from shaclapi.query import Query

logger = logging.getLogger(__name__)


class Reduction:
    def __init__(self, parser):
        self.parser = parser
        self.involvedShapesPerTarget = {}

    def reduce_shape_network(self, shapes, target_shape_list):
        involvedShapes = set()
        for target_shape in target_shape_list:
            shapeIds = list(self.parser.graph_traversal.traverse_graph(
                *self.parser.computeReducedEdges(shapes), target_shape))
            self.involvedShapesPerTarget[target_shape] = shapeIds
            involvedShapes = involvedShapes.union(shapeIds)
        logger.debug('Involved Shapes:' + str(self.involvedShapesPerTarget))
        shapes = [s for s in shapes if self.parser.shape_get_id(s) in involvedShapes]
        return shapes

    def replace_target_query(self, shapes, query, target_shapes, target_shape_list, merge_old_target_query, query_extension_per_target_shape):
        logger.info('Using Shape Schema WITH replaced target query!')
        if query_extension_per_target_shape is None:
            query_extension_per_target_shape = {}

        # Build target shape to variable mapping
        target_shapes_to_var = {}
        for var in target_shapes.keys():
            for target_shape in target_shapes[var]:
                target_shapes_to_var[target_shape] = var  # TODO: What is with a target shape occurring more then once?

        for s in shapes:
            s_id = self.parser.shape_get_id(s)
            if s_id in target_shape_list:
                # If there isn't a shape based on the target shape, reduce the target definition
                if len(target_shape_list) == 1 or s_id not in reduce(lambda a, b: a+b, [self.involvedShapesPerTarget[targetShape] for targetShape in target_shape_list if targetShape != s_id]):
                    # The Shape already has a target query
                    logger.debug(f'Reducing target definition of {s_id}')
                    logger.debug('Original Query:\n' + query.query_string)
                    if s.targetQuery and merge_old_target_query:
                        logger.debug('Old TargetDef: \n' + s.targetQuery)
                        oldTargetQuery = Query(s.targetQuery)
                        targetQuery = query.intersect(target_shapes_to_var[s_id], oldTargetQuery)
                    else:
                        if '?x' not in query.query_string:
                            new_query_string = query.query_string.replace(query.target_var, '?x')
                            targetQuery = Query(new_query_string).as_target_query('?x')
                        else:
                            targetQuery = query.query_string

                    def rreplace(s, old, new, occurrence):
                        li = s.rsplit(old, occurrence)
                        return new.join(li)

                    if s_id in query_extension_per_target_shape:
                        targetQuery = rreplace(targetQuery, '}', f'{query_extension_per_target_shape[s_id]}}}', 1)
                        logger.debug(f'Extended targetQuery with query extension specified!')

                    self.parser.replace_target_query(s, targetQuery)
                    logger.debug('New TargetDef:\n' + targetQuery)
    
    def node_order(self, target_shape_list):
        node_order = target_shape_list
        for target_shape in target_shape_list:
            node_order = node_order + list(self.involvedShapesPerTarget[target_shape])
    
        unique_node_order = []
        unique_nodes = set()
        for node in node_order:
            if node not in unique_nodes:
                unique_node_order.append(node)
                unique_nodes.add(node)
        logger.debug('Node Order estimated by the shaclapi: ' + str(unique_node_order))
        return unique_node_order
