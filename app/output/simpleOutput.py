from app.output.baseResult import BaseResult
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

    def __init__(self, baseResult, output=[]):
        self.base: BaseResult = baseResult
        self._output = output

    def to_json(self,targetShapeID):
        return json.dumps(self._output)

    def output(self):
        #TODO: eliminate duplicates
        if not self._output:
            transformed_report_triples = self.transform_report_triples()
            transformed_query_result = [{k: URIRef(v).n3(self.base.query.namespace_manager) for k,v in bindings.items()} for bindings in self.base.query_results]
            for b in transformed_query_result:
                pv_binding = {k: v for k, v in b.items() if '?' +
                              k in self.base.query.PV}
                triples = [(b[t[TripleE.SUBJECT][1:]], t[TripleE.PREDICATE], b.get(t[TripleE.OBJECT][1:]) or t[TripleE.OBJECT])
                           for t in self.base.query.get_triples(replace_prefixes=False) if t[TripleE.SUBJECT][1:] in b]
                report_triples = [
                    t for t in transformed_report_triples if t[0] in b.values()]

                self._output += [(pv_binding, triples, report_triples)]
        return self._output

    @staticmethod
    def fromJoinedResults(query, final_result_queue):
        output = []
        t_path = Namespace("//travshacl_path#")
        query.namespace_manager.bind('ts', t_path)
        t_path_valid = t_path['satisfiesShape'].n3(query.namespace_manager)
        t_path_invalid = t_path['violatesShape'].n3(query.namespace_manager)
        
        result = final_result_queue.get()
        while result != 'EOF':
            logger.debug("Result:" + str(result))
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

            #binding = {'?' + b['var']: URIRef(b['instance']).n3(query.namespace_manager) if "http" in b['instance'] else Literal(b['instance']) for b in query_result}
            logger.debug("Binding:" + str(binding))
            #filtered_bindings = {'?' + b['var']: URIRef(b['instance']).n3(query.namespace_manager) if "http" in b['instance'] else Literal(b['instance']) for b in query_result if '?' + b['var'] in query.PV}
            logger.debug("Filtered Binding:" + str(filtered_bindings))
            triples = [(binding[t[TripleE.SUBJECT]], t[TripleE.PREDICATE], binding.get(t[TripleE.OBJECT]) or t[TripleE.OBJECT])
                           for t in query.get_triples(replace_prefixes=False) if t[TripleE.SUBJECT] in binding]
            logger.debug("Triples:" + str(triples))
            report_triples = [(URIRef(b['instance']).n3(query.namespace_manager), (t_path_valid if b['validation'][1] else t_path_invalid), b['validation'][0])
                               for b in query_result if 'validation' in b and b['validation']]
            logger.debug("Report Triples:" + str(report_triples))
            output += [(filtered_bindings, triples, report_triples)]
            result = final_result_queue.get()
        return SimpleOutput(None, output)

    def __str__(self):
        if not self._output:
            self.output()
        string = "[\n"
        indent = 1
        for bindings, triples, report_triples in self._output:
            string += indent*" " + "{\n"
            indent += 1
            string += indent*" " + f"{list(bindings.items())},\n"

            string += indent*" " + "{\n"
            indent += 1
            for t in triples:
                string += indent*" " + f"{t},\n"
            indent -= 1
            string += indent*" " + "},\n"

            string += indent*" " + "{\n"
            indent += 1
            for t in report_triples:
                string += indent*" " + f"{t},\n"
            indent -= 1
            string += indent*" " + "},\n"
            indent -= 1
            string += indent*" " + "},\n"
        string += "]\n"
        return string

    def transform_report_triples(self):
        report_triples = []
        t_path = Namespace("//travshacl_path#")
        self.base.query.namespace_manager.bind('ts', t_path)
        t_path_valid = t_path['satisfiesShape'].n3(
            self.base.query.namespace_manager)
        t_path_invalid = t_path['violatesShape'].n3(
            self.base.query.namespace_manager)

        for instance, (shape, is_valid, reason) in self.base.validation_report_triples.items():
            report_triples += [(URIRef(instance).n3(self.base.query.namespace_manager),
                                t_path_valid if is_valid else t_path_invalid, shape)]
            # TODO: Add n['violatesConstraints']
        return report_triples
