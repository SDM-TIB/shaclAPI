# shaclAPI

The shaclAPI is a project meant to integrate the **SHACL** validation  into the **SPARQL** query execution. Given a knowledge graph a **SPARQL** query gives a set of solution mappings. The **SHACL** validation of a SHACL shape network over the knowledge graph gives validation results per pair of shape in the network and target entitiy assigned to the shape. The shaclAPI annotates the entities in the solution mappings with the validation result assigned by the SHACL validation. Further SHACL engine - agnostic heuristics are implemented, to reduce the overhead of the validation.
