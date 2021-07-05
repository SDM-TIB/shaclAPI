from rdflib.term import Variable, URIRef
from rdflib.namespace import RDF
from app.query import Query
import re, os
from app.output.CSVWriter import CSVWriter


class Connectivity():
    def __init__(self, query_object, endpoint) -> None:
        self.query = query_object
        self.endpoint = endpoint
        self.result_dict = []
        prefixes = {str(key): "<" + str(value) + ">" for (key, value) in self.query.namespace_manager.namespaces()}
        self.prefixString = "\n".join(["".join("PREFIX " + key + ":" + value) for (key, value) in prefixes.items()]) + "\n"

    def get_query_without_prefix(self):
        prefix_block = re.search(r'(PREFIX.*)SELECT', self.query.query_string, re.DOTALL)
        if prefix_block:
            query_without_prefix = Query(self.query.query_string[prefix_block.end(1):])
        else:
            query_without_prefix = self.query
        return query_without_prefix

    def URI(self, uri):
        if uri == 'a':
            return self.URI(RDF.type)
        if uri.startswith('<'):
            uri = uri[1:-1]
        if uri.startswith('^'):
            return '^'+URIRef(uri[1:]).n3(self.query.namespace_manager)
        else:
            return URIRef(uri).n3(self.query.namespace_manager)

    def query_endpoint(self, query):
        if "PREFIX" not in query:
            query = self.prefixString + query
        self.endpoint.setQuery(query)
        try:
            answer = self.endpoint.query().convert()
            return int(answer['results']['bindings'][0]['callret-0']['value'])
        except:
            raise Exception("Query {} lead to a failure!".format(query))

    def get_all_predicates(self, target_class):
        self.endpoint.setQuery(self.query_generator(target="DISTINCT ?p", subject_type=target_class, add_spo=True))
        answer = self.endpoint.query().convert()
        return set([self.URI(binding['p']['value']) for binding in answer['results']['bindings']])

    def get_predicates_between(self, class1, class2):
        self.endpoint.setQuery(self.query_generator(target="DISTINCT ?p", subject_type=class1, object_type=class2, add_spo=True))
        answer = self.endpoint.query().convert()
        return set([self.URI(binding['p']['value']) for binding in answer['results']['bindings']])

    def new_result(self, subject, predicate, object, num_conn):
        self.result_dict.append({"Class1": subject, "Predicate": predicate, "Class2": object, "Cardinality": num_conn})

    def write_to_file(self, path, clear=True):
        csv_writer = CSVWriter(path)
        csv_writer.writeListOfDicts(self.result_dict)
        if clear:
            self.result_dict = []

    def query_generator(self, target="COUNT(*)", subject_type=None, predicate=None, object_type=None, add_spo=False, extras=list()):
        return  self.prefixString + \
                f"SELECT {target} WHERE " + "{" + \
                    (f"?s a {subject_type}. \n" if subject_type else "") + \
                    (f"?s {predicate} ?o. \n" if predicate else "") + \
                    (f"?o a {object_type}. \n" if object_type else "") + \
                    ("?s ?p ?o. \n" if add_spo else "") + \
                    ("\n".join(extras)) + \
                "}"