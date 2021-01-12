#!/bin/bash

python3 main.py -d ./shapes/LUBM/all_target/3/ -a "http://localhost:14000/sparql" ./travshacl/univ1/all_target/3/bfs_S2S/1/ BFS --heuristics TARGET IN BIG --orderby --s2s
python3 main.py -d ./shapes/LUBM/all_target/3/ -a "http://localhost:14000/sparql" ./travshacl/univ1/all_target/3/bfs_selective_S2S/1/ BFS --heuristics TARGET IN BIG --selective --orderby --s2s
python3 main.py -d ./shapes/LUBM/all_target/3/ -a "http://localhost:14000/sparql" ./travshacl/univ1/all_target/3/bfs_selective_noVAL_S2S/1/ BFS --heuristics TARGET IN BIG --selective -m 0 --orderby --s2s
python3 main.py -d ./shapes/LUBM/all_target/3/ -a "http://localhost:14000/sparql" ./travshacl/univ1/all_target/3/bfs/1/ BFS --heuristics TARGET IN BIG --orderby

python3 main.py -d ./shapes/LUBM/all_target/7/ -a "http://localhost:14000/sparql" ./travshacl/univ1/all_target/7/bfs_S2S/1/ BFS --heuristics TARGET IN BIG --orderby --s2s
python3 main.py -d ./shapes/LUBM/all_target/7/ -a "http://localhost:14000/sparql" ./travshacl/univ1/all_target/7/bfs_selective_S2S/1/ BFS --heuristics TARGET IN BIG --selective --orderby --s2s
python3 main.py -d ./shapes/LUBM/all_target/7/ -a "http://localhost:14000/sparql" ./travshacl/univ1/all_target/7/bfs_selective_noVAL_S2S/1/ BFS --heuristics TARGET IN BIG --selective -m 0 --orderby --s2s
python3 main.py -d ./shapes/LUBM/all_target/7/ -a "http://localhost:14000/sparql" ./travshacl/univ1/all_target/7/bfs/1/ BFS --heuristics TARGET IN BIG --orderby
python3 main.py -d ./shapes/LUBM/all_target/7/ -a "http://localhost:14000/sparql" ./travshacl/univ1/all_target/7/dfs/1/ DFS --heuristics TARGET IN BIG --orderby
python3 main.py -d ./shapes/LUBM/all_target/7/ -a "http://localhost:14000/sparql" ./travshacl/univ1/all_target/7/bfs_selective/1/ BFS --heuristics TARGET IN BIG --selective --orderby
python3 main.py -d ./shapes/LUBM/all_target/7/ -a "http://localhost:14000/sparql" ./travshacl/univ1/all_target/7/dfs_selective/1/ DFS --heuristics TARGET IN BIG --selective --orderby

python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:14000/sparql" ./travshacl/univ1/all_target/14/bfs_S2S/1/ BFS --heuristics TARGET IN BIG --orderby --s2s
python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:14000/sparql" ./travshacl/univ1/all_target/14/bfs_selective_S2S/1/ BFS --heuristics TARGET IN BIG --selective --orderby --s2s
python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:14000/sparql" ./travshacl/univ1/all_target/14/bfs_selective_noVAL_S2S/1/ BFS --heuristics TARGET IN BIG --selective -m 0 --orderby --s2s
python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:14000/sparql" ./travshacl/univ1/all_target/14/bfs/1/ BFS --heuristics TARGET IN BIG --orderby
python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:14000/sparql" ./travshacl/univ1/all_target/14/dfs/1/ DFS --heuristics TARGET IN BIG --orderby

python3 main.py -d ./shapes/LUBM/some_targets/3/ -a "http://localhost:14000/sparql" ./travshacl/univ1/some_targets/3/bfs_S2S/1/ BFS --heuristics TARGET IN BIG --orderby --s2s
python3 main.py -d ./shapes/LUBM/some_targets/3/ -a "http://localhost:14000/sparql" ./travshacl/univ1/some_targets/3/bfs_selective_S2S/1/ BFS --heuristics TARGET IN BIG --selective --orderby --s2s
python3 main.py -d ./shapes/LUBM/some_targets/3/ -a "http://localhost:14000/sparql" ./travshacl/univ1/some_targets/3/bfs_selective_noVAL_S2S/1/ BFS --heuristics TARGET IN BIG --selective -m 0 --orderby --s2s
python3 main.py -d ./shapes/LUBM/some_targets/3/ -a "http://localhost:14000/sparql" ./travshacl/univ1/some_targets/3/bfs/1/ BFS --heuristics TARGET IN BIG --orderby
python3 main.py -d ./shapes/LUBM/some_targets/3/ -a "http://localhost:14000/sparql" ./travshacl/univ1/some_targets/3/dfs/1/ DFS --heuristics TARGET IN BIG --orderby

python3 main.py -d ./shapes/LUBM/some_targets/7/ -a "http://localhost:14000/sparql" ./travshacl/univ1/some_targets/7/bfs_S2S/1/ BFS --heuristics TARGET IN BIG --orderby --s2s
python3 main.py -d ./shapes/LUBM/some_targets/7/ -a "http://localhost:14000/sparql" ./travshacl/univ1/some_targets/7/bfs_selective_S2S/1/ BFS --heuristics TARGET IN BIG --selective --orderby --s2s
python3 main.py -d ./shapes/LUBM/some_targets/7/ -a "http://localhost:14000/sparql" ./travshacl/univ1/some_targets/7/bfs_selective_noVAL_S2S/1/ BFS --heuristics TARGET IN BIG --selective -m 0 --orderby --s2s
python3 main.py -d ./shapes/LUBM/some_targets/7/ -a "http://localhost:14000/sparql" ./travshacl/univ1/some_targets/7/bfs/1/ BFS --heuristics TARGET IN BIG --orderby
python3 main.py -d ./shapes/LUBM/some_targets/7/ -a "http://localhost:14000/sparql" ./travshacl/univ1/some_targets/7/dfs/1/ DFS --heuristics TARGET IN BIG --orderby

python3 main.py -d ./shapes/LUBM/some_targets/full/ -a "http://localhost:14000/sparql" ./travshacl/univ1/some_targets/14/bfs_S2S/1/ BFS --heuristics TARGET IN BIG --orderby --s2s
python3 main.py -d ./shapes/LUBM/some_targets/full/ -a "http://localhost:14000/sparql" ./travshacl/univ1/some_targets/14/bfs_selective_S2S/1/ BFS --heuristics TARGET IN BIG --selective --orderby --s2s
python3 main.py -d ./shapes/LUBM/some_targets/full/ -a "http://localhost:14000/sparql" ./travshacl/univ1/some_targets/14/bfs_selective_noVAL_S2S/1/ BFS --heuristics TARGET IN BIG --selective -m 0 --orderby --s2s
python3 main.py -d ./shapes/LUBM/some_targets/full/ -a "http://localhost:14000/sparql" ./travshacl/univ1/some_targets/14/bfs/1/ BFS --heuristics TARGET IN BIG --orderby
python3 main.py -d ./shapes/LUBM/some_targets/full/ -a "http://localhost:14000/sparql" ./travshacl/univ1/some_targets/14/dfs/1/ DFS --heuristics TARGET IN BIG --orderby



python3 main.py -d ./shapes/LUBM/all_target/3/ -a "http://localhost:15000/sparql" ./travshacl/univ8/all_target/3/bfs_S2S/1/ BFS --heuristics TARGET IN BIG --orderby --s2s
python3 main.py -d ./shapes/LUBM/all_target/3/ -a "http://localhost:15000/sparql" ./travshacl/univ8/all_target/3/bfs_selective_S2S/1/ BFS --heuristics TARGET IN BIG --selective --orderby --s2s
python3 main.py -d ./shapes/LUBM/all_target/3/ -a "http://localhost:15000/sparql" ./travshacl/univ8/all_target/3/bfs_selective_noVAL_S2S/1/ BFS --heuristics TARGET IN BIG --selective -m 0 --orderby --s2s
python3 main.py -d ./shapes/LUBM/all_target/3/ -a "http://localhost:15000/sparql" ./travshacl/univ8/all_target/3/bfs/1/ BFS --heuristics TARGET IN BIG --orderby
python3 main.py -d ./shapes/LUBM/all_target/3/ -a "http://localhost:15000/sparql" ./travshacl/univ8/all_target/3/dfs/1/ DFS --heuristics TARGET IN BIG --orderby

python3 main.py -d ./shapes/LUBM/all_target/7/ -a "http://localhost:15000/sparql" ./travshacl/univ8/all_target/7/bfs_S2S/1/ BFS --heuristics TARGET IN BIG --orderby --s2s
python3 main.py -d ./shapes/LUBM/all_target/7/ -a "http://localhost:15000/sparql" ./travshacl/univ8/all_target/7/bfs_selective_S2S/1/ BFS --heuristics TARGET IN BIG --selective --orderby --s2s
python3 main.py -d ./shapes/LUBM/all_target/7/ -a "http://localhost:15000/sparql" ./travshacl/univ8/all_target/7/bfs_selective_noVAL_S2S/1/ BFS --heuristics TARGET IN BIG --selective -m 0 --orderby --s2s
python3 main.py -d ./shapes/LUBM/all_target/7/ -a "http://localhost:15000/sparql" ./travshacl/univ8/all_target/7/bfs/1/ BFS --heuristics TARGET IN BIG --orderby
python3 main.py -d ./shapes/LUBM/all_target/7/ -a "http://localhost:15000/sparql" ./travshacl/univ8/all_target/7/dfs/1/ DFS --heuristics TARGET IN BIG --orderby
python3 main.py -d ./shapes/LUBM/all_target/7/ -a "http://localhost:15000/sparql" ./travshacl/univ8/all_target/7/bfs_selective/1/ BFS --heuristics TARGET IN BIG --selective --orderby
python3 main.py -d ./shapes/LUBM/all_target/7/ -a "http://localhost:15000/sparql" ./travshacl/univ8/all_target/7/dfs_selective/1/ DFS --heuristics TARGET IN BIG --selective --orderby

python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:15000/sparql" ./travshacl/univ8/all_target/14/bfs_S2S/1/ BFS --heuristics TARGET IN BIG --orderby --s2s
python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:15000/sparql" ./travshacl/univ8/all_target/14/bfs_selective_S2S/1/ BFS --heuristics TARGET IN BIG --selective --orderby --s2s
python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:15000/sparql" ./travshacl/univ8/all_target/14/bfs_selective_noVAL_S2S/1/ BFS --heuristics TARGET IN BIG --selective -m 0 --orderby --s2s
python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:15000/sparql" ./travshacl/univ8/all_target/14/bfs/1/ BFS --heuristics TARGET IN BIG --orderby
python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:15000/sparql" ./travshacl/univ8/all_target/14/dfs/1/ DFS --heuristics TARGET IN BIG --orderby

python3 main.py -d ./shapes/LUBM/some_targets/3/ -a "http://localhost:15000/sparql" ./travshacl/univ8/some_targets/3/bfs_S2S/1/ BFS --heuristics TARGET IN BIG --orderby --s2s
python3 main.py -d ./shapes/LUBM/some_targets/3/ -a "http://localhost:15000/sparql" ./travshacl/univ8/some_targets/3/bfs_selective_S2S/1/ BFS --heuristics TARGET IN BIG --selective --orderby --s2s
python3 main.py -d ./shapes/LUBM/some_targets/3/ -a "http://localhost:15000/sparql" ./travshacl/univ8/some_targets/3/bfs_selective_noVAL_S2S/1/ BFS --heuristics TARGET IN BIG --selective -m 0 --orderby --s2s
python3 main.py -d ./shapes/LUBM/some_targets/3/ -a "http://localhost:15000/sparql" ./travshacl/univ8/some_targets/3/bfs/1/ BFS --heuristics TARGET IN BIG --orderby
python3 main.py -d ./shapes/LUBM/some_targets/3/ -a "http://localhost:15000/sparql" ./travshacl/univ8/some_targets/3/dfs/1/ DFS --heuristics TARGET IN BIG --orderby

python3 main.py -d ./shapes/LUBM/some_targets/7/ -a "http://localhost:15000/sparql" ./travshacl/univ8/some_targets/7/bfs_S2S/1/ BFS --heuristics TARGET IN BIG --orderby --s2s
python3 main.py -d ./shapes/LUBM/some_targets/7/ -a "http://localhost:15000/sparql" ./travshacl/univ8/some_targets/7/bfs_selective_S2S/1/ BFS --heuristics TARGET IN BIG --selective --orderby --s2s
python3 main.py -d ./shapes/LUBM/some_targets/7/ -a "http://localhost:15000/sparql" ./travshacl/univ8/some_targets/7/bfs_selective_noVAL_S2S/1/ BFS --heuristics TARGET IN BIG --selective -m 0 --orderby --s2s
python3 main.py -d ./shapes/LUBM/some_targets/7/ -a "http://localhost:15000/sparql" ./travshacl/univ8/some_targets/7/bfs/1/ BFS --heuristics TARGET IN BIG --orderby
python3 main.py -d ./shapes/LUBM/some_targets/7/ -a "http://localhost:15000/sparql" ./travshacl/univ8/some_targets/7/dfs/1/ DFS --heuristics TARGET IN BIG --orderby

python3 main.py -d ./shapes/LUBM/some_targets/full/ -a "http://localhost:15000/sparql" ./travshacl/univ8/some_targets/14/bfs_S2S/1/ BFS --heuristics TARGET IN BIG --orderby --s2s
python3 main.py -d ./shapes/LUBM/some_targets/full/ -a "http://localhost:15000/sparql" ./travshacl/univ8/some_targets/14/bfs_selective_S2S/1/ BFS --heuristics TARGET IN BIG --selective --orderby --s2s
python3 main.py -d ./shapes/LUBM/some_targets/full/ -a "http://localhost:15000/sparql" ./travshacl/univ8/some_targets/14/bfs_selective_noVAL_S2S/1/ BFS --heuristics TARGET IN BIG --selective -m 0 --orderby --s2s
python3 main.py -d ./shapes/LUBM/some_targets/full/ -a "http://localhost:15000/sparql" ./travshacl/univ8/some_targets/14/bfs/1/ BFS --heuristics TARGET IN BIG --orderby
python3 main.py -d ./shapes/LUBM/some_targets/full/ -a "http://localhost:15000/sparql" ./travshacl/univ8/some_targets/14/dfs/1/ DFS --heuristics TARGET IN BIG --orderby




python3 main.py -d ./shapes/LUBM/all_target/3/ -a "http://localhost:16000/sparql" ./travshacl/univ32/all_target/3/bfs_S2S/1/ BFS --heuristics TARGET IN BIG --orderby --s2s
python3 main.py -d ./shapes/LUBM/all_target/3/ -a "http://localhost:16000/sparql" ./travshacl/univ32/all_target/3/bfs_selective_S2S/1/ BFS --heuristics TARGET IN BIG --selective --orderby --s2s
python3 main.py -d ./shapes/LUBM/all_target/3/ -a "http://localhost:16000/sparql" ./travshacl/univ32/all_target/3/bfs_selective_noVAL_S2S/1/ BFS --heuristics TARGET IN BIG --selective -m 0 --orderby --s2s

python3 main.py -d ./shapes/LUBM/all_target/7/ -a "http://localhost:16000/sparql" ./travshacl/univ32/all_target/7/bfs_S2S/1/ BFS --heuristics TARGET IN BIG --orderby --s2s
python3 main.py -d ./shapes/LUBM/all_target/7/ -a "http://localhost:16000/sparql" ./travshacl/univ32/all_target/7/bfs_selective_S2S/1/ BFS --heuristics TARGET IN BIG --selective --orderby --s2s
python3 main.py -d ./shapes/LUBM/all_target/7/ -a "http://localhost:16000/sparql" ./travshacl/univ32/all_target/7/bfs_selective_noVAL_S2S/1/ BFS --heuristics TARGET IN BIG --selective -m 0 --orderby --s2s

python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:16000/sparql" ./travshacl/univ32/all_target/14/bfs_S2S/1/ BFS --heuristics TARGET IN BIG --orderby --s2s
python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:16000/sparql" ./travshacl/univ32/all_target/14/bfs_selective_S2S/1/ BFS --heuristics TARGET IN BIG --selective --orderby --s2s
python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:16000/sparql" ./travshacl/univ32/all_target/14/bfs_selective_noVAL_S2S/1/ BFS --heuristics TARGET IN BIG --selective -m 0 --orderby --s2s

python3 main.py -d ./shapes/LUBM/some_targets/3/ -a "http://localhost:16000/sparql" ./travshacl/univ32/some_targets/3/bfs_S2S/1/ BFS --heuristics TARGET IN BIG --orderby --s2s
python3 main.py -d ./shapes/LUBM/some_targets/3/ -a "http://localhost:16000/sparql" ./travshacl/univ32/some_targets/3/bfs_selective_S2S/1/ BFS --heuristics TARGET IN BIG --selective --orderby --s2s
python3 main.py -d ./shapes/LUBM/some_targets/3/ -a "http://localhost:16000/sparql" ./travshacl/univ32/some_targets/3/bfs_selective_noVAL_S2S/1/ BFS --heuristics TARGET IN BIG --selective -m 0 --orderby --s2s

python3 main.py -d ./shapes/LUBM/some_targets/7/ -a "http://localhost:16000/sparql" ./travshacl/univ32/some_targets/7/bfs_S2S/1/ BFS --heuristics TARGET IN BIG --orderby --s2s
python3 main.py -d ./shapes/LUBM/some_targets/7/ -a "http://localhost:16000/sparql" ./travshacl/univ32/some_targets/7/bfs_selective_S2S/1/ BFS --heuristics TARGET IN BIG --selective --orderby --s2s
python3 main.py -d ./shapes/LUBM/some_targets/7/ -a "http://localhost:16000/sparql" ./travshacl/univ32/some_targets/7/bfs_selective_noVAL_S2S/1/ BFS --heuristics TARGET IN BIG --selective -m 0 --orderby --s2s

python3 main.py -d ./shapes/LUBM/some_targets/full/ -a "http://localhost:16000/sparql" ./travshacl/univ32/some_targets/14/bfs_S2S/1/ BFS --heuristics TARGET IN BIG --orderby --s2s
python3 main.py -d ./shapes/LUBM/some_targets/full/ -a "http://localhost:16000/sparql" ./travshacl/univ32/some_targets/14/bfs_selective_S2S/1/ BFS --heuristics TARGET IN BIG --selective --orderby --s2s
python3 main.py -d ./shapes/LUBM/some_targets/full/ -a "http://localhost:16000/sparql" ./travshacl/univ32/some_targets/14/bfs_selective_noVAL_S2S/1/ BFS --heuristics TARGET IN BIG --selective -m 0 --orderby --s2s




python3 main.py -d ./shapes/LUBM/all_target/3/ -a "http://localhost:17000/sparql" ./travshacl/univ256/all_target/3/bfs_S2S/1/ BFS --heuristics TARGET IN BIG --orderby --s2s
python3 main.py -d ./shapes/LUBM/all_target/3/ -a "http://localhost:17000/sparql" ./travshacl/univ256/all_target/3/bfs_selective_S2S/1/ BFS --heuristics TARGET IN BIG --selective --orderby --s2s
python3 main.py -d ./shapes/LUBM/all_target/3/ -a "http://localhost:17000/sparql" ./travshacl/univ256/all_target/3/bfs_selective_noVAL_S2S/1/ BFS --heuristics TARGET IN BIG --selective -m 0 --orderby --s2s

python3 main.py -d ./shapes/LUBM/all_target/7/ -a "http://localhost:17000/sparql" ./travshacl/univ256/all_target/7/bfs_S2S/1/ BFS --heuristics TARGET IN BIG --orderby --s2s
python3 main.py -d ./shapes/LUBM/all_target/7/ -a "http://localhost:17000/sparql" ./travshacl/univ256/all_target/7/bfs_selective_S2S/1/ BFS --heuristics TARGET IN BIG --selective --orderby --s2s
python3 main.py -d ./shapes/LUBM/all_target/7/ -a "http://localhost:17000/sparql" ./travshacl/univ256/all_target/7/bfs_selective_noVAL_S2S/1/ BFS --heuristics TARGET IN BIG --selective -m 0 --orderby --s2s

python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:17000/sparql" ./travshacl/univ256/all_target/14/bfs_S2S/1/ BFS --heuristics TARGET IN BIG --orderby --s2s
python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:17000/sparql" ./travshacl/univ256/all_target/14/bfs_selective_S2S/1/ BFS --heuristics TARGET IN BIG --selective --orderby --s2s
python3 main.py -d ./shapes/LUBM/all_target/full/ -a "http://localhost:17000/sparql" ./travshacl/univ256/all_target/14/bfs_selective_noVAL_S2S/1/ BFS --heuristics TARGET IN BIG --selective -m 0 --orderby --s2s

python3 main.py -d ./shapes/LUBM/some_targets/3/ -a "http://localhost:17000/sparql" ./travshacl/univ256/some_targets/3/bfs_S2S/1/ BFS --heuristics TARGET IN BIG --orderby --s2s
python3 main.py -d ./shapes/LUBM/some_targets/3/ -a "http://localhost:17000/sparql" ./travshacl/univ256/some_targets/3/bfs_selective_S2S/1/ BFS --heuristics TARGET IN BIG --selective --orderby --s2s
python3 main.py -d ./shapes/LUBM/some_targets/3/ -a "http://localhost:17000/sparql" ./travshacl/univ256/some_targets/3/bfs_selective_noVAL_S2S/1/ BFS --heuristics TARGET IN BIG --selective -m 0 --orderby --s2s

python3 main.py -d ./shapes/LUBM/some_targets/7/ -a "http://localhost:17000/sparql" ./travshacl/univ256/some_targets/7/bfs_S2S/1/ BFS --heuristics TARGET IN BIG --orderby --s2s
python3 main.py -d ./shapes/LUBM/some_targets/7/ -a "http://localhost:17000/sparql" ./travshacl/univ256/some_targets/7/bfs_selective_S2S/1/ BFS --heuristics TARGET IN BIG --selective --orderby --s2s
python3 main.py -d ./shapes/LUBM/some_targets/7/ -a "http://localhost:17000/sparql" ./travshacl/univ256/some_targets/7/bfs_selective_noVAL_S2S/1/ BFS --heuristics TARGET IN BIG --selective -m 0 --orderby --s2s

python3 main.py -d ./shapes/LUBM/some_targets/full/ -a "http://localhost:17000/sparql" ./travshacl/univ256/some_targets/14/bfs_S2S/1/ BFS --heuristics TARGET IN BIG --orderby --s2s
python3 main.py -d ./shapes/LUBM/some_targets/full/ -a "http://localhost:17000/sparql" ./travshacl/univ256/some_targets/14/bfs_selective_S2S/1/ BFS --heuristics TARGET IN BIG --selective --orderby --s2s
python3 main.py -d ./shapes/LUBM/some_targets/full/ -a "http://localhost:17000/sparql" ./travshacl/univ256/some_targets/14/bfs_selective_noVAL_S2S/1/ BFS --heuristics TARGET IN BIG --selective -m 0 --orderby --s2s
