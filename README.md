# shaclAPI

The shaclAPI is a project meant to integrate the **SHACL** validation  into the **SPARQL** query execution. Given a knowledge graph a **SPARQL** query gives a set of solution mappings. The **SHACL** validation of a SHACL shape schema over the knowledge graph gives validation results per pair of shape in the network and target entitiy assigned to the shape. The shaclAPI annotates the entities in the solution mappings with the validation result assigned by the SHACL validation. Further SHACL engine - agnostic heuristics are implemented, to reduce the overhead of the validation.

## Setup
The shaclAPI can be run as a webservice or can be used and extended by other projects by providing methods in the form of a library.
### Docker (run as a webservice)

### Library


## Configuration
The shaclAPI is highly configurable and supports the following options.
When using the shaclAPI as a webservice the options can be provided as parameters of the HTTP POST request to /multiprocessing.
Additionally an configuration file formatted as JSON can be provided with the config option. HTTP POST parameters will override the options configured in the configuration file.

| Required | Option | Default | Description |
|--------------| ------------ | --------- |------------ |
| x | query | - |The query to be executed over the SPARQL endpoint. |
| | target_shape / targetShape  | None |  The target shape selected for the given query and the given shape schema.  |
| x | external_endpoint | - | URL of the SPARQL endpoint the shape schema will be validated against. |
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
| | merge_old_target_query  | True | Whether the api should merge the query with the given target query in the target shape file. If this option is inactive the target query of the target shape is basically replaced with the star shaped query. |
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
|| query_extension_per_target_shape | None | For each given target shape a query extension can be given. The given query is extended, when merged or replaced with the target definition of the target shape. The query is extended by replacing the last '}' in the query with the extension followed by a '}'.|


