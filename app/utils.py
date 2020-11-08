import rdflib as rdflib
import app.globals as globals

def printSet(input):
    for elem in input:
        print(str(elem))
    if len(input) == 0:
        print("-")


def extend(term):
    index = term.rfind(":")
    extended_term = str(globals.namespaces[term[:index]]) + term[index+1:]
    return extended_term