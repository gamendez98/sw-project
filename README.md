# Project structure and usage

# Getting started

Before using this repo it is necessary to install all the packages described on the `requirements.txt` file. Also 

### schema.ttl

This file describes the ontologies for our project

## etl

This folder contains the scripts used to create the data for the neo4j database
and it is subdivided into:

### extraction

used to download data from different sources it can be used by running `python etl/extraction/main.py` . This script 
requires you to have a file `data/dict_split_4.json`. More information can be read on the file `etl/extraction/main.py`

### transform

used to download data from different sources it can be used by running `python etl/extraction/main.py`. This requires
to first run the extraction script. Also, you would need to run `docker run --rm --init --ulimit core=0 -p 8070:8070 grobid/grobid:0.8.0`
so that the grobid service is available. More information can be read on the file `etl/transform/main.py`

### load

To load the data into a `.rdf` you must run `python etl/load/load_instances.py` thi will produce a `project-schema.rdf`
file this can then be loaded into neo4j. To run this you require the files produced by the previous steps:

- `data/transform/semantic_web_project_data.h5`
- `data/extraction/semantic_scholar_authors.json`

