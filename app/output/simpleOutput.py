import json, logging
from rdflib import Namespace, URIRef, Literal
from app.triple import TripleE

logger = logging.getLogger(__name__)

class SimpleOutput():
    """
    bindings: (variable, subject)
    triples: (subject, path, object)
    report: (subject, ts:violatesShape, shape) / (subject, ts:satisfiesShape, shape) / (subject, ts:violatesConstraint, [constraints, ...])
    output: [([bindings, ...], [triples, ...], [report, ...])]
    """

    def __init__(self, output=None):
        self._output = output

    def to_json(self, targetShapeID=None):
        return json.dumps(self._output)

    @staticmethod
    def fromJoinedResults(query, final_result_queue):
        output = []
        t_path = Namespace("//travshacl_path#")
        query.namespace_manager.bind('ts', t_path)
        t_path_valid = t_path['satisfiesShape'].n3(query.namespace_manager)
        t_path_invalid = t_path['violatesShape'].n3(query.namespace_manager)
        
        result = final_result_queue.get()
        query_triples = query.get_triples(replace_prefixes=False)
        while result != 'EOF':
            #logger.debug("Result:" + str(result))
            query_result = result['result']

            # Create Bindings
            binding = {}
            filtered_bindings = {}
            for b in query_result:
                try:
                    instance = URIRef(b['instance']).n3(query.namespace_manager)
                except:
                    instance = b['instance']
                binding['?' + b['var']] = instance

                if '?' + b['var'] in query.PV:
                    filtered_bindings['?' + b['var']] = instance

            triples = [(binding[t[TripleE.SUBJECT]], t[TripleE.PREDICATE], binding.get(t[TripleE.OBJECT]) or t[TripleE.OBJECT])
                           for t in query_triples if t[TripleE.SUBJECT] in binding]
            report_triples = [(URIRef(b['instance']).n3(query.namespace_manager), (t_path_valid if b['validation'][1] else t_path_invalid), b['validation'][0])
                               for b in query_result if 'validation' in b and b['validation']]
            output += [(filtered_bindings, triples, report_triples)]
            result = final_result_queue.get()
        return SimpleOutput(output)
