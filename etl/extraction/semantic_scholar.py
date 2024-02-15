from enum import Enum
import requests
import json
from tqdm import tqdm

# %%

SEMANTIC_SCHOLAR_FIELDS = ",".join(
    ["corpusId", "title", "venue", "year", "authors", "abstract", "referenceCount", "citationCount",
     "influentialCitationCount", "isOpenAccess", "openAccessPdf", "fieldsOfStudy", "publicationTypes",
     "publicationDate", "journal", "authors", "citations", "references", ])


class SemanticURLs(str, Enum):
    SEARCH = 'https://api.semanticscholar.org/graph/v1/paper/autocomplete'
    DETAILS = 'https://api.semanticscholar.org/graph/v1/paper/{paper_id}'


# %%

def semantic_scholar_search_id(title: str) -> str | None:
    search_result = requests.get(SemanticURLs.SEARCH.value, params={'query': title})
    if search_result.status_code != 200:
        return None
    matches = search_result.json().get('matches', [])
    if matches:
        return matches[0]['id']


# %%
def semantic_scholar_details(idx: str) -> dict | None:
    if not idx:
        return None
    result = requests.get(SemanticURLs.DETAILS.format(paper_id=idx),
                          params={"fields": SEMANTIC_SCHOLAR_FIELDS})
    if result.status_code != 200:
        return None
    return result.json()


def write_results():
    with (open('data/dict_split_4.json', 'r') as input_file,
          open('data/extraction/semantic_scholar_visited.txt', 'r') as visited_keys_file):
        visited_keys = {key.strip() for key in visited_keys_file.readlines()}
        initial_source = json.load(input_file)
    with (open('data/extraction/semantic_scholar_results.json', 'a') as output_file,
          open('data/extraction/semantic_scholar_visited.txt', 'a') as visited_keys_file):
        for key, data in tqdm(initial_source.items(), total=len(initial_source), desc='retrieving semantic scholar'):
            if key in visited_keys:
                continue
            title = data['title']
            result = semantic_scholar_details(semantic_scholar_search_id(title))
            if result:
                output_file.write(json.dumps(result))
                output_file.write('\n')
            visited_keys_file.write(key)
            visited_keys_file.write('\n')




# %%

if __name__ == '__main__':
    write_results()
