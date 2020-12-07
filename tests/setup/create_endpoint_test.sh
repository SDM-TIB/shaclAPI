#!/bin/bash

sudo docker stop test_graph
sudo docker rm test_graph
sudo docker run --name test_graph -p 14000:8890 -v "$(pwd)/TestData:/data/toLoad" -d kemele/virtuoso:7-stable
