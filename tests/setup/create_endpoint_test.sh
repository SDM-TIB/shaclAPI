#!/bin/bash
if [ $# -gt 1 ]; then
    path="$(pwd)/TestData"
else
    path=$1
fi
sudo docker stop test_graph
sudo docker rm test_graph
sudo docker run --name test_graph -p 14000:8890 -v "$path:/data/toLoad" -d kemele/virtuoso:7-stable
