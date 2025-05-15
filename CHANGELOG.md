# v0.12.0 - 15 May 2925
- update dependencies
- drop Python 3.8 support

# v0.11.1 - 03 Sep 2024
- update dependencies

# v0.11.0 - 23 Nov 2023
- require a newer version of Trav-SHACL (>= 1.7.0)
- fix endpoint creation due to changes in Trav-SHACL v1.6.0
- enable passing of RDFlib graphs instead of schema directory (Trav-SHACL v1.7.0)
- add Python 3.12 support

# v0.10.0 - 07 Aug 2023
- update dependencies
- update test cases
- add ability to pass a config dictionary instead of config file path
- fix invalid escape sequences
- set reduced network to be one connected component
- include only unidirectional dependencies in reduced network
- add feature for removing constraints when parsing TTL
- add license
- fix issues when parsing OR constraints
- add possibility to remove constraints from within an OR constraint
- deal with inverse paths when removing constraints

# v0.9.8 - 27 Jun 2023
- update dependencies
- remove print command when setting up logger
- add Python 3.11 support

# v0.9.7 - 06 Feb 2023
- set default shape format to SHACL, i.e., using RDF for the shape definitions; following the SHACL specification
- require a newer version of Trav-SHACL (>= 1.2.0)

# v0.9.6 - 29 Sep 2022
- prevent validation for empty SHACL shape schema
- overlap: fix division by zero

# v0.9.5 - 28 Sep 2022
- enable target query rewriting for non-star-shaped queries

# v0.9.4 - 27 Sep 2022
- capture only basic statistics
- by default, store no output of the SHACL validator

# v0.9.3 - 27 Sep 2022
- add functionality to compute the overlap of the reduced shape schemas for two given shapes

# v0.9.2 - 22 Sep 2022
- fix missing module Xgoptional
- relaxed dependencies

# v0.9.1 - 26 Aug 2022
- code style improvements
- relaxed dependencies
- same features for service and library

# v0.9.0 - 04 Aug 2022
- first published version