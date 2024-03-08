import json
from enum import Enum
from typing import List

import requests

from etl.extraction.utils import checkpoint_extraction, retry, initial_extraction_input_loader

# %%

API_KEY = ""

# %%

SEMANTIC_SCHOLAR_FIELDS = ",".join(
    ["corpusId", "title", "venue", "year", "authors", "abstract", "referenceCount", "citationCount",
     "influentialCitationCount", "isOpenAccess", "openAccessPdf", "fieldsOfStudy", "publicationTypes",
     "publicationDate", "journal", "authors", "citations", "references", "externalIds"])

SEMANTIC_SCHOLAR_AUTHOR_FIELDS = ",".join(
    ["authorId", "externalIds", "url", "name", "aliases", "affiliations", "homepage", "paperCount", "citationCount",
     "hIndex", ]
)


class SemanticURLs(str, Enum):
    SEARCH = 'https://api.semanticscholar.org/graph/v1/paper/autocomplete'
    DETAILS = 'https://api.semanticscholar.org/graph/v1/paper/{paper_id}',
    BATCH = 'https://api.semanticscholar.org/graph/v1/paper/batch'
    AUTHOR_BATCH = 'https://api.semanticscholar.org/graph/v1/author/batch'


# %%

@retry()
def id_request(title: str):
    return requests.get(SemanticURLs.SEARCH.value, params={'query': title}, headers={"x-api-key": API_KEY})


@retry()
def details_request(idx: str):
    return requests.get(SemanticURLs.DETAILS.format(paper_id=idx), params={"fields": SEMANTIC_SCHOLAR_FIELDS},
                        headers={"x-api-key": API_KEY})


@retry()
def author_batch_request(ids: List[str]):
    return requests.post(SemanticURLs.AUTHOR_BATCH.value, params={'fields': SEMANTIC_SCHOLAR_AUTHOR_FIELDS},
                         json={"ids": ids})


@retry()
def batch_request(ids: List[str]):
    return requests.post(SemanticURLs.BATCH.value, params={'fields': SEMANTIC_SCHOLAR_FIELDS},
                         json={"ids": ids})


# %%

def semantic_scholar_search_id(title: str) -> str | None:
    search_result = id_request(title)
    if search_result.status_code == 404:
        return None
    if search_result.status_code == 200:
        matches = search_result.json().get('matches', [])
        if matches:
            return matches[0]['id']


# %%

def semantic_scholar_batch_details(ids: List[str]):
    if not ids:
        return []
    results = batch_request(ids)
    if results.status_code != 200:
        return []
    return [result for result in results.json() if result]


# %%

def semantic_scholar_batch_author_details(ids: List[str]):
    if not ids:
        return []
    results = author_batch_request(ids)
    if results.status_code != 200:
        return []
    return [result for result in results.json() if result]


# %%
def semantic_scholar_details(idx: str) -> dict | None:
    if not idx:
        return None
    result = details_request(idx)
    if result.status_code == 404:
        return None
    return result.json()


# %%

def semantic_scholar_entry_mapper(data_entries):
    ids = [semantic_scholar_search_id(data_entry['title']) for data_entry in data_entries]
    ids = [i for i in ids if i]
    return semantic_scholar_batch_details(ids)


# %%

def semantic_scholar_author_loader(input_path: str):
    with open(input_path, 'r') as input_file:
        for line in input_file.readlines():
            paper = json.loads(line)
            for author in paper['authors']:
                if author['authorId']:
                    yield author['authorId'], author


# %%

def semantic_scholar_author_mapper(data_entries):
    ids = [author['authorId'] for author in data_entries]
    return semantic_scholar_batch_author_details(ids)


# %%

# 1
def initial_extraction_scholar():
    checkpoint_extraction(
        input_file_path='data/dict_split_3.json',
        visited_keys_path='data/extraction/semantic_scholar_visited.txt',
        output_path='data/extraction/semantic_scholar_results.json',
        entry_mapper=semantic_scholar_entry_mapper,
        input_loader=initial_extraction_input_loader,
        batch_size=100
    )


# 2
def author_extraction_scholar():
    checkpoint_extraction(
        input_file_path='data/extraction/semantic_scholar_results.json',
        visited_keys_path='data/extraction/visited_authors.txt',
        output_path='data/extraction/semantic_scholar_authors.json',
        entry_mapper=semantic_scholar_author_mapper,
        input_loader=semantic_scholar_author_loader,
        batch_size=100
    )
