import re
from rdflib.namespace import RDF
from rdflib.plugins import sparql
from rdflib.paths import InvPath
from rdflib.term import URIRef
from app.triple import Triple

class Query:
    target_query = None

    def __init__(self, query_string, target_var=None):
        self.query_string = query_string
        self.__query_object = None
        self.__namespace_manager = None
        self.__variables = None
        self.__PV = None
        self.__triples = None
        self.__target_var = target_var

    @property
    def query_object(self):
        if not self.__query_object:
            self.__query_object = sparql.processor.prepareQuery(self.query_string)
        return self.__query_object

    @property
    def triples(self):
        if not self.__triples:
            self.__triples = self.extract_triples()
        return self.__triples
    
    @property
    def target_var(self):
        if not self.__target_var:
            self.__target_var = self._get_target_var()
        return self.__target_var

    @property
    def namespace_manager(self):
        if not self.__namespace_manager:
            self.__namespace_manager = self.query_object.prologue.namespace_manager
        return self.__namespace_manager

    @property
    def variables(self):
        if not self.__variables:
            variables = self.query_object.algebra.get('_vars') or []
            self.__variables = [var.n3(self.namespace_manager) for var in variables]
        return self.__variables

    @property
    def PV(self):
        if not self.__PV:
            PV = self.query_object.algebra.get('PV') or []
            self.__PV = [var.n3(self.namespace_manager) for var in PV]
        return self.__PV

    @staticmethod
    def prepare_query(query):
        """Query must be slightly modified to fit the conditions of travshacl, rdflib, ...

        Args:
            query (string): Initial select query

        Returns:
            Query: Valid Query-Object for further processing
        """
        #Remove ',' in a query (esp.: SELECT ?x, ?y). RDFLib is not able to parse these patterns.
        query = query.replace(',', ' ')
        #Literals are parsed in the format '"literal_value"', ' must be replace with " to apply pattern matching.
        query = query.replace('\'', '"')
        #Remove '.' if it is followed by '}', tarvshacl cannot handle these dots.
        query = re.sub(r'\.[\s\n]*}', r'\n}', query)
        return Query(query)
        
    def extract_triples(self):
        """Entry point for a recursive run over a sparql.algebra, which represents a query as nested dictionaries.
        Returns:
            list: List of triples (s, p, o) where each term is given by its internal rdflib representation (e.g.: Variable('?subject'))
        """
        return self.__extract_triples_recursion(self.query_object.algebra)    

    def extract_filter_terms(self):
        return re.findall('FILTER\(.*\)',self.query_string,re.DOTALL)     

    def __extract_triples_recursion(self, algebra, is_optional=False):
        """Recursive function for triple pattern extraction.

        Args:
            algebra (dict): A sparql.algebra dictionary

        Returns:
            list: List of Triple Objects which behave as Python Tuple (s, p, o) where each term is given by its internal rdflib representation (e.g.: Variable('?subject'))
        """
        result = []
        for k,v in algebra.items():
            if isinstance(v, dict):
                if v.name == "LeftJoin" and v['expr'].name == "TrueFilter" and v['expr']['_vars'] == set():
                    result = result + self.__extract_triples_recursion(v, is_optional= True)
                else:
                    if is_optional and k == "p2":
                        result = result + self.__extract_triples_recursion(v, is_optional= True)
                    else:
                        result = result + self.__extract_triples_recursion(v, is_optional= False)
            else:
                if k == 'triples':
                    result = result + Triple.fromList(v, is_optional)
        return result

    def _get_target_var(self):
        """Retrieves the target_variable of a star-shaped query.
        Given by the star-shaped structure, the target_variable must appear in each triple of the query.

        Raises:
            Exception: If this function retrieves multiple or no candidates, the query is assumed to be a non-valid query.

        Returns:
            string: target_variable
        """
        candidates = set(self.variables)
        for t in self.get_triples(replace_prefixes=False):
            candidates = set(t) & candidates
            if len(candidates) == 1:
                return candidates.pop()
            if len(candidates) == 0:
                break
        if '?x' in self.variables:
            return '?x'
        raise Exception("Not a valid star-shaped query.")

    def as_target_query(self, replace_prefixes=True):
        """Creates a target query based on the given query_string, 
        where the projection is reduced to the target_var only and 
        (optionally) the prefixes are replaced and removed.

        Args:
            replace_prefixes (bool, optional): Highlights if prefixes should be replaced or not. Defaults to True.

        Returns:
            string: A target query corresponding to the query_string
        """
        if not self.target_query:      
            self.target_query = self._reduce_select(self.query_string)
        if replace_prefixes:
            return self._replace_prefixes_in_query(self.target_query)
        return self.target_query

    def merge_as_target_query(self, oldTargetQuery):
        '''
        Merges two queries; such that one gets a minimal result:
        1.) Rename the old target var to the new target var.
        2.) Retain all filters
        3.) If we have a optional version of a triple and a not optional version. Convert all optionals to non optionals.
        4.) Eliminate all duplicate triples, which are not needed in the filters.
        '''
        # Step 1
        old_query_string_renamed = oldTargetQuery.as_valid_query().replace(oldTargetQuery.target_var, self.target_var)
        oldQuery = Query(old_query_string_renamed)

        # Step 2
        new_filters = self.extract_filter_terms()
        old_filters = oldQuery.extract_filter_terms()

        # Step 3 + 4
        final_triples = set()

        for t in self.triples:
            if t.optional:
                if t.not_optional_self() in oldQuery.triples:
                    final_triples.add(t.not_optional_self())
                else:
                    final_triples.add(t)
            else:
                final_triples.add(t)
        
        for t in oldQuery.triples:
            if t.optional:
                if t.not_optional_self() in self.triples:
                    final_triples.add(t.not_optional_self())
                else:
                    final_triples.add(t)
            else:
                final_triples.add(t)
        
        target_query_string = "SELECT {} WHERE".format(self.target_var) + \
            " {\n" + "\n".join([t.n3(self.namespace_manager) for t in final_triples]) + \
            "\n" + "\n".join([filter for filter in (new_filters + old_filters)]) + "}"

        return Query.prepare_query(target_query_string).query_string


    def as_valid_query(self):
        """Returns the query as a valid query_string. 
        Is is assumed that each Query-Object is created via prepare_query(), 
        then the query_string itself is already a valid query_string.
        Otherwise, this will NOT return a valid_query.
        TODO: This is just a getter for self.query_string, make sure that it returns always a valid version of a query.

        Returns:
            string: A valid query_string
        """
        return self.query_string

    def as_result_query(self):
        return re.sub(
            r'(SELECT\s+(DISTINCT|REDUCED)?).*WHERE', 
            f'SELECT DISTINCT * WHERE',
            self.query_string
        )

    def _reduce_select(self, query):
        """
        Reduces the full SELECT part of the target_query to the relevant target var.
        Regex based on: https://www.w3.org/TR/rdf-sparql-query/#select
        Regex: SELECT [DISTINCT|REDUCED] [[?targ, ...]|*] WHERE -> SELECT [DISTINCT|REDUCED] ?targ WHERE
        """
        query = re.sub(
            r'(SELECT\s+(DISTINCT|REDUCED)?).*WHERE', 
            f'SELECT DISTINCT {self.target_var} WHERE',
            query
        )
        return query
    
    def _replace_prefixes_in_query(self, query):
        """Uses the information from self.get_triples to replace abbreviated term with their long version.
        It would be possible to perform this action without knowing the triples, 
        but finding and replacing only relevant parts is then harder.

        Args:
            query (string): A query in prefix/abbreviated notation

        Returns:
            string: A query in IRI/long notation
        """
        for short_list, long_list in zip(self.get_triples(replace_prefixes=False), self.get_triples(replace_prefixes=True)):
            short_s, short_p, short_o = short_list
            long_s , long_p , long_o  = long_list
            short_triple = f'{re.escape(short_s)}\s+{re.escape(short_p)}\s+{re.escape(short_o)}'
            long_triple  = f'{long_s} {long_p} {long_o}'
            query = re.sub(short_triple, long_triple, query)
        
        prefix_block = re.search(r'(PREFIX.*)SELECT', query, re.DOTALL)
        query = query[prefix_block.end(1):]
        return query

    def get_predicates(self, replace_prefixes=True, ignore_inv=True):
        """Returns a list of all predicates appearing in the query_string. 
        Optionally replacing prefixes and/or ignoring the paths' directions.

        Args:
            replace_prefixes (bool, optional): Highlights whether prefixes should be replaced or not. Defaults to True.
            ignore_inv (bool, optional): Highlights whether path directions can be ignored. Defaults to True.

        Returns:
            list(string): A list of all predicates/paths
        """
        if ignore_inv:
            return [p[p.startswith('^'):] for _, p, _ in self.get_triples(replace_prefixes=replace_prefixes)]
        return [p for _, p, _ in self.get_triples(replace_prefixes=replace_prefixes)]

    def get_triples(self, replace_prefixes=True):
        """Returns a list of all triples appearing in the query_string.
        Optionally replacing prefixes.

        Args:
            replace_prefixes (bool, optional): Highlights whether prefixes should be replaced or not. Defaults to True.

        Returns:
            list: A list of all triples where each triple is a tuple or three strings ('subject', 'predicate', 'object)
        """
        if replace_prefixes:
            return [(s.n3(), p.n3(), o.n3()) for s, p, o in self.triples]
        triples = []
        for s, p, o in self.triples:
            s = s.n3(self.namespace_manager)
            #InvPath's n3() is not capable of handling namespace_managers
            if isinstance(p, InvPath):
                p = '^'+URIRef(p.arg).n3(self.namespace_manager)
            #rdf:type is commonly written as 'a' and therefore replaced.
            elif p == RDF.type:
                p = 'a'
            else:
                p = p.n3(self.namespace_manager)
            o = o.n3(self.namespace_manager)
            triples += [(s, p, o)]

        return triples
