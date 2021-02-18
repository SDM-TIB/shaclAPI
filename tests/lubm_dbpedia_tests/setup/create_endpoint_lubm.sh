#!/bin/bash

sudo docker run --name lubm_univ8 -p 14000:8890 -v "$(pwd)/Univ8:/data/toLoad" -d kemele/virtuoso:7-stable
