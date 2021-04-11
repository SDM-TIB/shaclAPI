#!/bin/bash

python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:14000/sparql" ./output/1/ns_v/ BFS --heuristics TARGET IN BIG
python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:14000/sparql" ./output/1/ns_nv/ BFS --heuristics TARGET IN BIG -m 0
python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:14000/sparql" ./output/1/s_v/ BFS --heuristics TARGET IN BIG --selective
python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:14000/sparql" ./output/1/s_nv/ BFS --heuristics TARGET IN BIG --selective -m 0

python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:15000/sparql" ./output/8/ns_v/ BFS --heuristics TARGET IN BIG
python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:15000/sparql" ./output/8/ns_nv/ BFS --heuristics TARGET IN BIG -m 7
python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:15000/sparql" ./output/8/s_v/ BFS --heuristics TARGET IN BIG --selective
python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:15000/sparql" ./output/8/s_nv/ BFS --heuristics TARGET IN BIG --selective -m 7

python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:16000/sparql" ./output/32/ns_v/ BFS --heuristics TARGET IN BIG
python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:16000/sparql" ./output/32/ns_nv/ BFS --heuristics TARGET IN BIG -m 31
python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:16000/sparql" ./output/32/s_v/ BFS --heuristics TARGET IN BIG --selective
python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:16000/sparql" ./output/32/s_nv/ BFS --heuristics TARGET IN BIG --selective -m 31

python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:17000/sparql" ./output/256/s_v/ BFS --heuristics TARGET IN BIG --selective
python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:17000/sparql" ./output/256/s_nv/ BFS --heuristics TARGET IN BIG --selective -m 255