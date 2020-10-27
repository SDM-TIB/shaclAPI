#!/bin/bash
CONSTRUCT_QUERY=$(<constructquery.sparql)
QUERY=$(<query.sparql)

curl -X POST -H "Accept:application/sparql-results+json" --data-urlencode "query=$CONSTRUCT_QUERY" http://127.0.0.1:5000/constructQuery
sleep 2s
curl -X POST -H "Accept:application/sparql-results+json" --data-urlencode "query=$QUERY" http://127.0.0.1:5000/endpoint 2>&1 >/dev/null
sleep 2s
python3 travshacl/main.py -d ./shapes/3 -a http://localhost:5000/endpoint ./output/ BFS --heuristics TARGET IN BIG --orderby --selective
