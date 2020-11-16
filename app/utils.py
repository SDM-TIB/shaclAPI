import rdflib as rdflib
import app.globals as globals

def printSet(input):
    for elem in input:
        print(str(elem))
    if len(input) == 0:
        print("-")

def pathToString(paths):
    result = ""
    for path in paths:
        result = result + '\n['
        for triple in path:
            result = result + str(triple) + ','
        result = result[0:-1] + ']'
    return result


def extend(term):
    index = term.rfind(":")
    extended_term = str(globals.namespaces[term[:index]]) + term[index+1:]
    return extended_term