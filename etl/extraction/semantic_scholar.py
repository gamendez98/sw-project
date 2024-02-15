from enum import Enum
import requests

from etl.extraction.utils import initial_extraction, retry

# %%

SEMANTIC_SCHOLAR_FIELDS = ",".join(
    ["corpusId", "title", "venue", "year", "authors", "abstract", "referenceCount", "citationCount",
     "influentialCitationCount", "isOpenAccess", "openAccessPdf", "fieldsOfStudy", "publicationTypes",
     "publicationDate", "journal", "authors", "citations", "references", ])


class SemanticURLs(str, Enum):
    SEARCH = 'https://api.semanticscholar.org/graph/v1/paper/autocomplete'
    DETAILS = 'https://api.semanticscholar.org/graph/v1/paper/{paper_id}'


# %%

@retry()
def id_request(title: str):
    return requests.get(SemanticURLs.SEARCH.value, params={'query': title})


@retry()
def details_request(idx: str):
    return requests.get(SemanticURLs.DETAILS.format(paper_id=idx), params={"fields": SEMANTIC_SCHOLAR_FIELDS})


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
def semantic_scholar_details(idx: str) -> dict | None:
    if not idx:
        return None
    result = details_request(idx)
    if result.status_code == 404:
        return None
    return result.json()


# %%

def semantic_scholar_entry_mapper(data_entry):
    return semantic_scholar_details(semantic_scholar_search_id(data_entry['title']))


# %%

if __name__ == '__main__':
    initial_extraction(
        'data/dict_split_3.json',
        'data/extraction/semantic_scholar_visited.txt',
        'data/extraction/semantic_scholar_results.json',
        entry_mapper=semantic_scholar_entry_mapper)
    # TODO: extract information from citations, references and authors
