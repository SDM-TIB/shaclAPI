#!/bin/bash
if [ $# -gt 0 ]; then
    path=$1
else
    path="$(pwd)/TestData"
fi
sudo docker stop test_graph
sudo docker rm test_graph
sudo docker run --name test_graph -p 14000:8890 -v "$path:/data/toLoad" -d kemele/virtuoso:7-stable
