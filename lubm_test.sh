QUERY=$(<lubm_query_1.sparql)

curl -X POST -H "Accept:application/sparql-results+json" -d "task=a" -d "traversalStrategie=DFS" -d "schemaDir=./shapes/lubm" -d "heuristic=TARGET IN BIG" -d "query=$QUERY" -d "targetShape=FullProfessor"  http://127.0.0.1:5000/go 
