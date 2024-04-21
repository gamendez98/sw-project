# Project structure and usage

# Getting started

Before using this repo it is necessary to install all the packages described on the `requirements.txt` file. Also 

### schema.ttl

This file describes the ontologies for our project

## etl

This folder contains the scripts used to create the data for the neo4j database
and it is subdivided into

### extraction

used to download data from different sources it can be used by running `python etl/extraction/main.py` . This script 
requires you to have a file `data/dict_split_4.json`. More information
can be read on the file itself 

### transform



### load

To load the data into a `.rdf` you must run `python etl/load/load_instances.py` thi will produce a `project-schema.rdf`
file this can then be loaded into neo
