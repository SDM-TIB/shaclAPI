from app.output.baseResult import BaseResult
import json
from rdflib import Namespace, URIRef
from app.triple import TripleE


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

    def to_json(self):
        return json.dumps(self._output)

    def output(self):
        #TODO: eliminate duplicates
        if not self._output:
            transformed_report_triples = self.transform_report_triples()
            transformed_query_result = [{k: URIRef(v).n3(self.base.query.namespace_manager) for k,v in bindings.items()} for bindings in self.base.query_results]
            for b in transformed_query_result:
                pv_binding = {k: v for k, v in b.items() if '?' +
                              k in self.base.query.PV}
                triples = [(b[t[TripleE.SUBJECT][1:]], t[TripleE.PREDICAT], b.get(t[TripleE.OBJECT][1:]) or t[TripleE.OBJECT])
                           for t in self.base.query.get_triples(replace_prefixes=False) if t[TripleE.SUBJECT][1:] in b]
                report_triples = [
                    t for t in transformed_report_triples if t[0] in b.values()]

                self._output += [(pv_binding, triples, report_triples)]
        return self._output

    @staticmethod
    def fromJoinedResults(result_list, query):
        output = []
        t_path = Namespace("//travshacl_path#")
        query.namespace_manager.bind('ts', t_path)
        t_path_valid = t_path['satisfiesShape'].n3(query.namespace_manager)
        t_path_invalid = t_path['violatesShape'].n3(query.namespace_manager)
        
        for query_result in result_list:
            binding = {'?' + b['var']:URIRef(b['instance']).n3(query.namespace_manager) for b in query_result}
            filtered_bindings = {'?' + b['var']:URIRef(b['instance']).n3(query.namespace_manager) for b in query_result if '?' + b['var'] in query.PV}

            triples = [(binding[t[TripleE.SUBJECT]], t[TripleE.PREDICAT], binding.get(t[TripleE.OBJECT]) or t[TripleE.OBJECT])
                           for t in query.get_triples(replace_prefixes=False) if t[TripleE.SUBJECT] in binding]
            report_triples = [(URIRef(b['instance']).n3(query.namespace_manager), (t_path_valid if b['validation'][1] else t_path_invalid), b['validation'][0])
                               for b in query_result if 'validation' in b and b['validation']]
            output += [(filtered_bindings, triples, report_triples)]
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
