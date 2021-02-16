from rdflib.plugins import sparql
from app.triple import Triple
from app.tripleStore import TripleStore
from rdflib import term
import json
from rdflib.plugins.sparql.parserutils import CompValue
import re
from app.utils import printSet
import app.path as Path

'''
Representation of a query.
Using the rdflib each query is parsed into an algebra term.
The Algebra Term is used to extract triples and used when executing a query over a local ConjunctivGraph.
'''
class Query:

    def __init__(self,in_query: str):
        idx = re.finditer('\?\S+,',in_query) # Only remove , separating vars
        idx = list(idx)
        last_idx = 0
        self.query = ''
        for match in idx:
            comma_index = match.end()
            self.query = self.query + in_query[last_idx : comma_index - 1]
            last_idx = comma_index
        self.query = self.query + in_query[last_idx:]
        self.query = self.query.replace("AND", "&&")
        self.__parsed_query = None
        self.__triples = None
        self.__filters = None

    @property
    def parsed_query(self):
        if self.__parsed_query == None:
            self.__parsed_query = sparql.processor.prepareQuery(self.query)
        return self.__parsed_query
    
    def triples(self,normalized = False):
        if self.__triples == None:
            self.__triples = [Triple(*t) for t in self.extract_triples()]
        if normalized:
            return [t.normalized(t) for t in self.__triples]
        return self.__triples

    @property
    def queriedVars(self):
        result = []
        try:
            result = self.parsed_query.algebra['PV']
        except Exception:
            pass
        finally:
            return result
    @property
    def vars(self):
        result=[]
        try:
            result = list(self.parsed_query.algebra['_vars'])
        except Exception:
            pass
        finally:
            return result

    def extract_triples(self):
        list_of_triples = self.__extract_triples_rekursion(self.parsed_query.algebra)
        return list_of_triples

    def __extract_triples_rekursion(self, algebra: dict):
        result = []
        for k,v in algebra.items():
            if isinstance(v, dict):
                result = result + self.__extract_triples_rekursion(v)
            else:
                if k == 'triples':
                    result = result + v
        return result
    
    def __str__(self):
        return self.query

    def dumpAlgebra(self,path):
        with open(path,'w') as f:
            json.dump(str(self.parsed_query.algebra),f, indent=1)
    
    @property
    def filters(self):
        if self.__filters == None:
            parsed_algebra = self.parsed_query.algebra
            result_filter = self.__getFilter(parsed_algebra)
            self.__filters = result_filter[0]
        return self.__filters
     

    def __getFilter(self,algebra: dict):
        result = list()
        count = 0
        for k,v in algebra.items():
            if isinstance(v, CompValue) and v.name == 'Filter':
                result = result + [self.__expressionFromFilter(v['expr'])]
                count = count + 1
                rek_result = self.__getFilter(v)
                result = result + rek_result[0]
                count = count + rek_result[1]
            elif isinstance(v, CompValue):
                rek_result = self.__getFilter(v)
                result = result + rek_result[0]
                count = count + rek_result[1]
        return (result,count)
    
    def __expressionFromFilter(self, filter_expr):
        result = list()
        if isinstance(filter_expr, CompValue) and filter_expr.name == 'RelationalExpression':
            result.append((filter_expr['expr'], filter_expr['op'], filter_expr['other']))
        elif isinstance(filter_expr, CompValue) and 'ConditionalAndExpression' in filter_expr.name:
            result = result + self.__expressionFromFilter(filter_expr['expr'])
            for expr in filter_expr['other']:
                result = result + self.__expressionFromFilter(expr)
        else:
            return []
        return result
    
    def variablesInFilter(self):
        result = []
        filters = self.filters
        if filters:
            for expression in filters:
                result = result + self.__variablesInFilter(expression)
            return result
        else:
            return list()

    def __variablesInFilter(self,expression):
        result = list()
        if isinstance(expression,dict):
            for key,value in expression.items():
                result = result + self.__variablesInFilter(value)
        elif isinstance(expression,list) or isinstance(expression, tuple):
            for item in expression:
                result = result + self.__variablesInFilter(item)
        elif isinstance(expression,term.Variable):
            return [expression]
        return result
         
    def simplify(self):
        expr = self.filters
        if len(expr) == 0:
            query_string = 'SELECT DISTINCT ' 
            for var in self.queriedVars:
                query_string = query_string + var.n3() + ' '
            query_string = query_string + 'WHERE {\n'
            for triple in self.triples():
                query_string = query_string + triple.n3() + '\n'
            query_string = query_string + '} ORDER BY ?x'
            return Query(query_string)
        elif len(expr) == 1:
            query_string = 'SELECT DISTINCT ' 
            for var in self.queriedVars:
                query_string = query_string + var.n3() + ' '
            query_string = query_string + 'WHERE {\n'
            for triple in self.triples():
                query_string = query_string + triple.n3() + '\n'
            filter_term = ''
            for triple in expr[0]:
                if not triple[1] in ['!=','=']:
                    return self
                filter_term = filter_term + triple[0].n3() + ' ' + triple[1] + ' '+ triple[2].n3() + ' && '
            filter_term = filter_term[:-3]
            query_string = query_string + 'FILTER( '+ filter_term + ' )\n'
            query_string = query_string + '} ORDER BY ?x'
            return Query(query_string)
        else:
            return self            

    @classmethod
    def constructQueryFrom(self,targetShape, initial_query_triples, path, shape_id, filter_clause):
        if targetShape != shape_id:
            where_clause = TripleStore.fromSet(initial_query_triples).n3() + Path.pathToAbbreviatedString(path) + TripleStore(shape_id).n3(optionals=True)
            query = 'CONSTRUCT {\n' + TripleStore(shape_id).n3(normalized=True) + '} WHERE {\n' + where_clause + filter_clause +'}'
        else:
            query = 'CONSTRUCT {\n' + TripleStore.fromSet(initial_query_triples).n3(normalized=True) + '} WHERE {\n' + TripleStore.fromSet(initial_query_triples).n3() + filter_clause + '}'
        return self(query)
    
    @classmethod
    def targetDefFromStarShapedQuery(self, initial_query_triples, filter_clause):
        # Identify ?x
        if filter_clause == '':
            return Query('SELECT ?x WHERE {\n' + TripleStore.fromSet(initial_query_triples).n3(prepending_point = False) + filter_clause + '}')
        else:
            return Query('SELECT ?x WHERE {\n' + TripleStore.fromSet(initial_query_triples).n3(prepending_point = True) + filter_clause + '}')

        #count_dict = {var.n3(): initial_query.query.count(var.n3()) for var in initial_query.vars}


