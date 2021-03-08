from rdflib import Namespace, URIRef

class QueryReport:
    """
    bindings: (variable, subject)
    triples: (subject, path, object)
    report: (subject, ts:violatesShape, shape) / (subject, ts:satisfiesShape, shape) / (subject, ts:violatesConstraint, [constraints, ...])
    output: [([bindings, ...], [triples, ...], [report, ...])]
    """

    def __init__(self, report, query, results):
        self._full_report = []
        self.query = query
        self.namespace_manager = query.namespace_manager

        self.bindings = self.parse_results(results)
        self.triples = self.parse_triples(query)
        self.report_triples = self.parse_report(report)

    def __str__(self):
        string = "[\n"
        indent = 1
        for bindings, triples, report_triples in self.full_report:
            string += indent*" " + f"{{ {list(bindings.items())} }},\n"
            
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
        string += "]\n"
        return string

    @property
    def full_report(self):
        if not self._full_report:
            for b in self.bindings:
                pv_binding = {k: v for k,v in b.items() if '?'+k in self.query.PV}
                triples = [(b[t[0][1:]], t[1], b.get(t[2][1:]) or t[2]) for t in self.triples if t[0][1:] in b]
                report_triples = [t for t in self.report_triples if t[0] in b.values()]

                self._full_report += [(pv_binding, triples, report_triples)]
        return self._full_report

    @staticmethod
    def create_output(report, query, results):
        return QueryReport(report, query, results).full_report

    def parse_results(self, results):
        # Transforms the given bindings into a list of bindings using prefix notation
        return [{k: URIRef(v['value']).n3(self.namespace_manager) for k, v in entry.items()} for entry in results['results']['bindings']]

    def parse_triples(self, query):
        return query.get_triples(replace_prefixes=False)

    def parse_report(self, report):
        #Maybe create RDF Graph?
        report_triples = []
        t_path = Namespace("//travshacl_path#")
        self.namespace_manager.bind('ts', t_path)
        for shape, s_report in report.items():
            if s_report.get('valid_instances'):
                for validating_shape, instance, _ in s_report['valid_instances']:
                    instance = URIRef(instance).n3(self.namespace_manager)
                    path = t_path['satisfiedShape'].n3(self.namespace_manager)
                    report_triples += [(instance, path, validating_shape)]
            if s_report.get('invalid_instances'):
                for violating_shape,  instance, _ in s_report['invalid_instances']:
                    instance = URIRef(instance).n3(self.namespace_manager)
                    path = t_path['satisfiedShape'].n3(self.namespace_manager)
                    report_triples += [(instance, path, violating_shape)]
                    #TODO: Add n['violatesConstraints']
        return report_triples
