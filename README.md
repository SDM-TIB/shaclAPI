[![Tests](https://github.com/SDM-TIB/shaclAPI/actions/workflows/test.yml/badge.svg)](https://github.com/SDM-TIB/shaclAPI/actions/workflows/test.yml)

# shaclAPI

The shaclAPI is a project meant to integrate the **SHACL** validation  into the **SPARQL** query execution. Given a knowledge graph a **SPARQL** query gives a set of solution mappings. The **SHACL** validation of a SHACL shape schema over the knowledge graph gives validation results per pair of shape in the network and target entitiy assigned to the shape. The shaclAPI annotates the entities in the solution mappings with the validation result assigned by the SHACL validation. Further SHACL engine - agnostic heuristics are implemented, to reduce the overhead of the validation.

## Setup
### Webservice
#### Docker
In order to run the shaclAPI, build the Docker image from the source code:

``docker build . -t juliangercke/shaclAPI:latest``

Once the Docker image is built, you can start the shaclAPI:

``docker run --name api -d -p 9999:5000 juliangercke/shaclAPI:latest``

The shaclAPI will be reachable at http://localhost:9999. For the following examples execute:

``API=localhost:9999``

#### Docker Compose
A docker-compose file is provided, therefore the shaclAPI can be run using:

``docker-compose up --build -d``

The shaclAPI will be accessible at http://localhost:9999. For the following examples execute:

``API=localhost:9999``

#### Python
To run the shaclAPI directly using python 3.8.11 with the flask development server, the python dependencies need to be installed:

``pip install -r requirements.txt``

Depending on the operating system ``start.bat`` or ``start.sh`` can now be used to start the shaclAPI.
The shaclAPI will be accessible at http://localhost:5000. For the following examples execute:

``API=localhost:5000``

### Library
To use the shaclAPI as a library it is recommended to use python 3.8.11, however other versions might work as well.
Install the python dependencies using: ``pip install -r requirements.txt``

## Usage
### Webservice
You can use the shaclAPI by making HTTP requests. The following describes the different API calls:

#### GET: /
Returns ``Hello World`` and should be used to check whether the API is running or not.

Example call:
```bash
curl -X GET $API/
```
#### POST: /multiprocessing
This is the main API call, used to send a query to the SPARQL endpoint and simultaneously execute the SHACL validation to validate the query results.
There are various options, which can be provided as parameters of the HTTP POST request. Additionally an configuration file formatted as JSON can be provided with the config option. HTTP POST parameters will override the options configured in the configuration file.

Example configuration:
```json
{
    "external_endpoint": "http://dbpedia.org/sparql",
    "query": "PREFIX dbo:<http://dbpedia.org/ontology/>\nPREFIX dbr:<http://dbpedia.org/resource/>\nPREFIX dbp:<http://dbpedia.org/property/>\nSELECT DISTINCT ?x WHERE {\n    ?x a dbo:Film. \n ?x dbp:studio dbr:Walt_Disney_Pictures\n}",
    "schemaDir": "./examples/dbpedia/shapes/",
    "targetShape": "MovieShape",
    "backend": "travshacl",
    "output_format": "simple"
}
```

Example call:
```bash
curl -X POST -d "config=./examples/dbpedia/config.json" $API/multiprocessing
```

Example output:
```json
[
	[
		{"?x": "dbr:Tex_(film)"},  # The query result given in the form of the original SPARQL bindings
		[ # Triples to explain the SPARQL bindings
			["dbr:Tex_(film)", "dbp:studio", "dbr:Walt_Disney_Pictures"], 
			["dbr:Tex_(film)", "a", "dbo:Film"], 
			["dbr:Tex_(film)", "dbo:imdbId", "<0084783>"], 
			["dbr:Tex_(film)", "dbo:starring", "dbr:Matt_Dillon"]
		], 
		[ # The validation result assigned to the SPARQL bindings. Each entity occuring in the SPARQL bindings can violate (ts:violatesShape) or satisfy (ts:satisfiesShape) a given instance:
			["dbr:Tex_(film)", "ts:violatesShape", "MovieShape"]
		]
	], 
	[
		{"?x": "dbr:Night_Crossing"}, 
		[
			["dbr:Night_Crossing", "dbp:studio", "dbr:Walt_Disney_Pictures"], 
			["dbr:Night_Crossing", "a", "dbo:Film"], 
			["dbr:Night_Crossing", "dbo:imdbId", "<0082810>"], 
			["dbr:Night_Crossing", "dbo:starring", "dbr:Doug_McKeon"]
		], 
		[
			["dbr:Night_Crossing", "ts:violatesShape", "MovieShape"]
		]
	], ...
]
```
There are further examples provided in the ``examples`` directory.

#### POST: /validation
This API call can be used to execute the SHACL validation  over the given SPARQL endpoint, while reducing the workload using the given heuristics and give the number of valid/invalid instances per Shape. There are various options, which can be provided as parameters of the HTTP POST request. Additionally an configuration file formatted as JSON can be provided with the config option. HTTP POST parameters will override the options configured in the configuration file. 

Using the same configuration as with ``/multiprocessing``:

Example call:
```bash
curl -X POST -d "config=./examples/dbpedia/config.json" $API/validation
```

Example output:
```json
{"MovieShape":{"invalid":50,"valid":0}}
```


#### POST: /reduce
This API call can be used to retrieve the shape names of the reduced shape schema given a starting shape.
The options for this call can be provided as parameters of the HTTP POST request or as a JSON file using the config option.
HTTP POST parameters will override the options configured in the configuration file.

Example call:
```bash
curl -X POST -d "schemaDir=./examples/lubm/shapes/" -d "targetShape=Department" $API/reduce
```

Example output:
```json
{"shapes":["Department","University"]}
```


### Library

See the available sphinx documentation: [https://sdm-tib.github.io/shaclAPI/html/index.html](https://sdm-tib.github.io/shaclAPI/html/index.html)

## Configuration
The shaclAPI is highly configurable and supports the following options.

| Required | Option | Default | Description |
|--------------| ------------ | --------- |------------ |
| x | query | - |The query to be executed over the SPARQL endpoint. |
| | target_shape / targetShape  | None |  The target shape selected for the given query and the given shape schema.  |
| x | external_endpoint | - | The URL of the SPARQL endpoint, which contains the data to be validated and retrieved. |
| x | schema_directory | - | The directory containing the shape files (.ttl or .json) |
| | config | None | The path to a json formatted configuration file. Has to be absolute or relative w.r.t. run.py.  |
| | output_directory | ./output/ | The directory which will be used by the SHACL engine and the shaclAPI to save the validation output and statistics to files (depending on the other configurations) |
| | shape_format / shapeFormat  | JSON | The format of the shape files. Can be JSON or TTL |
| | work_in_parallel / workInParallel | False |  Whether the SHACL engine should work in parallel |
| | use_selective_queries / useSelectiveQueries | True | Whether the SHACL engine should use more selective queries. |
| | maxSplit | 256 | The maximal number of entities in FILTER or VALUES clause of a SPARQL query, used by the SHACL engine. |
| | order_by_in_queries | True | Whether the SHACL engine should use queries with a ORDER BY clause. |
| | backend | travshacl | The SHACL engine, which will be used by the shaclAPI. |
| | traversal_strategy / traversalStrategy | DFS | The traversal strategy used by the backend to reduce the shape graph and by the backend to find the execution order. Can be DFS or BFS. |
| | heuristic | TARGET IN BIG | Only if Trav-SHACL is used as backend. The heuristic used to determine the validation order of the shapes. |
| | replace_target_query | True | Whether or not the shaclAPI should replace the target query of the target shape.|
| | start_with_target_shape | True | Whether the SHACL engine is forced to start the validation process with the target shape. |
| | start_shape_for_validation | None | The shape which is used as starting point for the validation in the backend. It will override the start point determined by the SHACL engine (in case of Trav-SHACL) and only applies if start_with_target_shape is false)|
| | merge_old_target_query  | True | Whether the shaclAPI should merge the query with the given target query in the target shape file. If this option is inactive the target query of the target shape is basically replaced with the star shaped query. |
| | remove_constraints  | False |  Whether the shaclAPI should remove constraints of the target shape not mentioned in the query. |
| | output_format  | simple  | Which output format the api should use. This can be "test" or "simple". |
| | memory_size | 100000000 | Number of tuples, which can be stored in main memory during the join process. |
| | prune_shape_network  |  True |  Whether or not prune the shape schema to the shapes reachable from the target shapes.|
| | test_identifier | random uuid1 | The test identifier will be used in output files identifing the run. |
| | run_in_serial | False | This option can be turned on to force the steps of the shaclAPI to be executed in serial. |
| | reasoning | True | This option will turn reasoning in terms of extended output on and off. |
| | use_pipes | False |  Whether to use pipes during the multiprocessing. Otherwise the shaclAPI will use queues.|
| | collect_all_validation_results | False | Whether to collect all validation results for each mapping. Otherwise at least one validation result is collected for each given target_shape. Collecting all results will make the approach blocking. |
|| write_stats | True |  Whether to write statistics to the output directory. |
|| outputs | False | Whether to save the validation output of the backend to a file. |
|| query_extension_per_target_shape | None | For each given target shape a query extension can be given. The given query is extended, when merged or replaced with the target definition of the target shape. The query is extended by replacing the last '}' in the query with the extension followed by a '}'.|


