#!/bin/bash
QUERY=$(<query.sparql)

#python3 travshacl/main.py -d ./shapes/3 -a http://dbpedia.org/sparql ./output/ BFS --heuristics TARGET IN BIG --orderby --selective --query "$QUERY" --targetDef MovieShape

curl -X POST -H "Accept:application/sparql-results+json" -d "task=a" -d "traversalStrategie=DFS" -d "schemaDir=./shapes/3" -d "heuristic=TARGET IN BIG" -d "query=$QUERY" -d "targetShape=MovieShape"  http://127.0.0.1:5000/go 

#python3 travshacl/main.py -d ./shapes/3 -a http://localhost:5000/endpoint ./output/ BFS --heuristics TARGET IN BIG --orderby --selective
