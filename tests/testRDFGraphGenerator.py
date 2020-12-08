from rdflib import Namespace
from rdflib.term import URIRef, Literal
import names
from rdflib import ConjunctiveGraph
from rdflib.namespace import RDF
import random


# Testcase 1:
# Used Shapes:
# - Person
# - BigFamily
# 

#  Shape Name     # Target Class        # Constraints                             #
# --------------- # ------------------- # --------------------------------------  # 
# Person          # test:person         # test:age -- min: 1                      # 
#                 #                     # test:age -- max: 1                      #
#                 #                     # test:member_of -- min: 1 shape: Family  #
# ------------------------------------------------------------------------------- #
# SmallFamily     # test:family         # ^test:member_of -- min: 2 shape: Person #
#                 #                     # ^test:member_of -- max: 2 shape: Person #
# ------------------------------------------------------------------------------- #
# AverageFamily   # test:family         # ^test:member_of -- min: 3 shape: Person #
#                 #                     # ^test:member_of -- max: 5 shape: Person #
# ------------------------------------------------------------------------------- #
# BigFamily       # test:family         # ^test:member_of -- min: 6 shape: Person #
#                 #                     # ^test:member_of -- max: 6 shape: Person #


# Namespace Definitions
NAMESPACE = Namespace("http://example.org/testGraph/") 
PROPERTIES_NAMESPACE = Namespace(NAMESPACE['class'] + '#') # short test:
FAMILY_NAMESPACE = Namespace(NAMESPACE['family'] + '/')
PERSON_NAMESPACE = Namespace(NAMESPACE['person'] + '/')

graph = ConjunctiveGraph()

NUMBER_OF_FAMILIES = 1000
AVERAGE_PERSONS_PER_FAMILIY = 4
BIG_FAMILY_SIZE = 6
SMALL_FAMILY_SIZE = 2 

def fillUp(set_input, soll):
    ist = len(set_input)
    result = set_input.copy()
    while len(result) < soll:
        result.add(random.choice(list(set_input)) + '_' + str(random.randint(1,100)))
    return result

# Data
families = fillUp(set([names.get_last_name() for i in range(NUMBER_OF_FAMILIES)]), NUMBER_OF_FAMILIES)
persons = fillUp(set([names.get_first_name() for i in range(AVERAGE_PERSONS_PER_FAMILIY*NUMBER_OF_FAMILIES)]), AVERAGE_PERSONS_PER_FAMILIY* NUMBER_OF_FAMILIES)

print('Created {} families! '.format(len(families)))
print('Created {} person! '.format(len(persons)))

# Create Families
for name in families:
    graph.add((FAMILY_NAMESPACE[name], RDF.type, PROPERTIES_NAMESPACE['family']))

# Create Persons
for vorname in persons:
    graph.add((PERSON_NAMESPACE[vorname], RDF.type, PROPERTIES_NAMESPACE['person']))
    graph.add((PERSON_NAMESPACE[vorname], PROPERTIES_NAMESPACE['age'], Literal(random.randint(10,100))))
    

# Put Half of Persons into Families
person_iter = iter(persons)
family_iter = iter(families)

# Average Size
print('Creating {} average families'.format(int(NUMBER_OF_FAMILIES/4)))
for i in range(int(NUMBER_OF_FAMILIES/4)):
    actual_family = family_iter.__next__()
    for j in range(AVERAGE_PERSONS_PER_FAMILIY):
        graph.add((PERSON_NAMESPACE[person_iter.__next__()],PROPERTIES_NAMESPACE['member_of'],FAMILY_NAMESPACE[actual_family]))


# Small
print('Creating {} small families'.format(int(NUMBER_OF_FAMILIES/8)))
for i in range(int(NUMBER_OF_FAMILIES/8)):
    actual_family = family_iter.__next__()
    for j in range(SMALL_FAMILY_SIZE):
        graph.add((PERSON_NAMESPACE[person_iter.__next__()],PROPERTIES_NAMESPACE['member_of'],FAMILY_NAMESPACE[actual_family]))


# Big
print('Creating {} big families'.format(int(NUMBER_OF_FAMILIES/8)))
for i in range(int(NUMBER_OF_FAMILIES/8)):
    actual_family = family_iter.__next__()
    for j in range(BIG_FAMILY_SIZE):
        graph.add((PERSON_NAMESPACE[person_iter.__next__()],PROPERTIES_NAMESPACE['member_of'],FAMILY_NAMESPACE[actual_family]))

# Rest are Singles --> here Singles don't belong to a Family

# Save Graph to file
with open("tests/setup/TestData/families2.owl", "wb") as f:
    f.write(graph.serialize(format='pretty-xml'))