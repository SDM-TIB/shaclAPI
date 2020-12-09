# -*- coding: utf-8 -*-
prefixes = {
    "ub": "<http://swat.cse.lehigh.edu/onto/univ-bench.owl#>",
    "test1": "<http://example.org/testGraph1#>",
    "test2": "<http://example.org/testGraph2#>",
    "test3": "<http://example.org/testGraph3#>",
    "test4": "<http://example.org/testGraph4#>",
    "rdf": "<http://www.w3.org/1999/02/22-rdf-syntax-ns#>",
    "dbo": "<http://dbpedia.org/ontology/>",
    "dbr": "<http://dbpedia.org/resource/>",
    "yago": "<http://dbpedia.org/class/yago/>",
    "foaf": "<http://xmlns.com/foaf/0.1/>",
    "": "<http://example.org/>"
}

prefixString = "\n".join(["".join("PREFIX " + key + ":" + value) for (key, value) in prefixes.items()]) + "\n"


def getPrefixString():
    return prefixString

def getPrefixes():
    return prefixes