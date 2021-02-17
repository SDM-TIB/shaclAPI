from rdflib import Namespace

class QueryReport:
    _full_report = []

    """
    bindings: (variable, subject)
    triples: (subject, path, object)
    report: (subject, ts:violatesShape, shape) / (subject, ts:satisfiesShape, shape) / (subject, ts:violatesConstraint, [constraints, ...])
    output: [([bindings, ...], [triples, ...], [report, ...])]
    """

    def __init__(self, report, query, results):
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
                triples = [(b[t[0].replace('?','')], t[1], b.get(t[2].replace('?','')) or t[2]) for t in self.triples if t[0].replace('?','') in b]
                report_triples = [t for t in self.report_triples if t[0] in b.values()]

                self._full_report += [(b, triples, report_triples)]
        return self._full_report

    @staticmethod
    def create_output(report, query, results):
        return QueryReport(report, query, results)

    def parse_results(self, results):
        slim_result = [x for x in results['results']['bindings']]
        return [{k: v['value']  for k, v in entry.items()} for entry in slim_result]

    def parse_triples(self, query):
        return [(t.subject.n3(), t.predicat.n3(), t.object.n3()) for t in query.triples()]


    def parse_report(self, report):
        #Maybe create RDF Graph?
        report_triples = []
        n = Namespace("//travshacl_path#")
        for shape, s_report in report.items():
            print(s_report.get('valid_instances') is not None, s_report.get('invalid_instances') is not None)
            if s_report.get('valid_instances'):
                for validating_shape, instance, _ in s_report['valid_instances']:
                    report_triples += [(instance, n['satisfiesShape'], validating_shape)]
            if s_report.get('invalid_instances'):
                for violating_shape,  instance, _ in s_report['invalid_instances']:
                    report_triples += [(instance, n['violatesShape'], violating_shape)]
                    #TODO: Add n['violatesConstraints']
        return report_triples
