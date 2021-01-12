#!/bin/bash

python3 main.py -d ./shapes/LUBM/all_target/3/ -a "http://localhost:14000/sparql" ./output/refact6/8_30/small/ DFS --heuristics TARGET IN BIG --orderby --selective
python3 main.py -d ./shapes/LUBM/all_target/3/ -a "http://localhost:14001/sparql" ./output/refact6/8_50/small/ DFS --heuristics TARGET IN BIG --orderby --selective
python3 main.py -d ./shapes/LUBM/all_target/3/ -a "http://localhost:14002/sparql" ./output/refact6/8_70/small/ DFS --heuristics TARGET IN BIG --orderby --selective

python3 main.py -d ./shapes/LUBM/all_target/3/ -a "http://localhost:14003/sparql" ./output/refact6/32_30/small/ DFS --heuristics TARGET IN BIG --orderby --selective
python3 main.py -d ./shapes/LUBM/all_target/3/ -a "http://localhost:14004/sparql" ./output/refact6/32_50/small/ DFS --heuristics TARGET IN BIG --orderby --selective
python3 main.py -d ./shapes/LUBM/all_target/3/ -a "http://localhost:14005/sparql" ./output/refact6/32_70/small/ DFS --heuristics TARGET IN BIG --orderby --selective

python3 main.py -d ./shapes/LUBM/all_target/3/ -a "http://localhost:14006/sparql" ./output/refact6/256_30/small/ DFS --heuristics TARGET IN BIG --orderby --selective
python3 main.py -d ./shapes/LUBM/all_target/3/ -a "http://localhost:14007/sparql" ./output/refact6/256_50/small/ DFS --heuristics TARGET IN BIG --orderby --selective
python3 main.py -d ./shapes/LUBM/all_target/3/ -a "http://localhost:14008/sparql" ./output/refact6/256_70/small/ DFS --heuristics TARGET IN BIG --orderby --selective




python3 main.py -d ./shapes/LUBM/all_target/7/ -a "http://localhost:14000/sparql" ./output/refact6/8_30/medium/ DFS --heuristics TARGET IN BIG --orderby --selective
python3 main.py -d ./shapes/LUBM/all_target/7/ -a "http://localhost:14001/sparql" ./output/refact6/8_50/medium/ DFS --heuristics TARGET IN BIG --orderby --selective
python3 main.py -d ./shapes/LUBM/all_target/7/ -a "http://localhost:14002/sparql" ./output/refact6/8_70/medium/ DFS --heuristics TARGET IN BIG --orderby --selective

python3 main.py -d ./shapes/LUBM/all_target/7/ -a "http://localhost:14003/sparql" ./output/refact6/32_30/medium/ DFS --heuristics TARGET IN BIG --orderby --selective
python3 main.py -d ./shapes/LUBM/all_target/7/ -a "http://localhost:14004/sparql" ./output/refact6/32_50/medium/ DFS --heuristics TARGET IN BIG --orderby --selective
python3 main.py -d ./shapes/LUBM/all_target/7/ -a "http://localhost:14005/sparql" ./output/refact6/32_70/medium/ DFS --heuristics TARGET IN BIG --orderby --selective

python3 main.py -d ./shapes/LUBM/all_target/7/ -a "http://localhost:14006/sparql" ./output/refact6/256_30/medium/ DFS --heuristics TARGET IN BIG --orderby --selective
python3 main.py -d ./shapes/LUBM/all_target/7/ -a "http://localhost:14007/sparql" ./output/refact6/256_50/medium/ DFS --heuristics TARGET IN BIG --orderby --selective
python3 main.py -d ./shapes/LUBM/all_target/7/ -a "http://localhost:14008/sparql" ./output/refact6/256_70/medium/ DFS --heuristics TARGET IN BIG --orderby --selective




python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:14000/sparql" ./output/refact6/8_30/big/ DFS --heuristics TARGET IN BIG --orderby --selective
python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:14001/sparql" ./output/refact6/8_50/big/ DFS --heuristics TARGET IN BIG --orderby --selective
python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:14002/sparql" ./output/refact6/8_70/big/ DFS --heuristics TARGET IN BIG --orderby --selective

python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:14003/sparql" ./output/refact6/32_30/big/ DFS --heuristics TARGET IN BIG --orderby --selective
python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:14004/sparql" ./output/refact6/32_50/big/ DFS --heuristics TARGET IN BIG --orderby --selective
python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:14005/sparql" ./output/refact6/32_70/big/ DFS --heuristics TARGET IN BIG --orderby --selective

python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:14006/sparql" ./output/refact6/256_30/big/ DFS --heuristics TARGET IN BIG --orderby --selective
python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:14007/sparql" ./output/refact6/256_50/big/ DFS --heuristics TARGET IN BIG --orderby --selective
python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:14008/sparql" ./output/refact6/256_70/big/ DFS --heuristics TARGET IN BIG --orderby --selective