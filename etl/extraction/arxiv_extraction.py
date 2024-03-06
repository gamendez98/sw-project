import json
import random
import time
from typing import Callable

from tqdm import tqdm

from enum import Enum
from typing import List

import requests

import arxiv, re
from unidecode import unidecode

def batched(iterable, n=1, skip=None):
    r = []
    for ndx in iterable:
        if skip and skip(ndx):
            continue
        r.append(ndx)
        if len(r) == n:
            yield r
            r = []
    yield r

def initial_extraction(input_file_path: str, visited_keys_path: str, output_path: str, entry_mapper: Callable, batch_size: int = 30):
    '''
    Initial data extraction. Write results and entries already visited from input file
    :param input_file_path: the source provided by the teacher
    :param visited_keys_path: stores the already visited entries
    :param output_path: results as a list of jsons to be read like
        `results = [json.loads(entry) for entry in f.readlines()]`
    :param entry_mapper: function that takes the data provided by the teacher and returns the data provided by the API
    :return: None
    '''

    def save_results(rs, ks, out, visited):
        for result in rs:
            if result:
                out.write(json.dumps(result))
                out.write('\n')
        for k in ks:
            visited.write(k)
            visited.write('\n')

    with (open(input_file_path, 'r') as input_file,
          open(visited_keys_path, 'r') as visited_keys_file):
        visited_keys = {key.strip() for key in visited_keys_file.readlines()}
        initial_source = json.load(input_file)
        initial_source = [(k, d) for k, d in initial_source.items()]
        initial_source = initial_source[::-1]
    with (open(output_path, 'a') as output_file,
          open(visited_keys_path, 'a') as visited_keys_file):
        batches = batched(initial_source, n=batch_size, skip=(lambda x: x[0] in visited_keys))
        for batch in tqdm(batches, total=int((len(initial_source) - len(visited_keys)) / batch_size),
                          desc='retrieving arxiv'):
            keys = [k for k, _ in batch]
            datums = [d for _, d in batch]
            results = entry_mapper(datums)
            save_results(results, keys, output_file, visited_keys_file)

def normalize(texto: str) -> str:
    texto_limpio = re.sub(r'\d+\.\d+-\d+\.\d+\|', '', texto)
    texto_limpio = re.sub(r'[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ ]', '', texto_limpio)
    texto_limpio = texto_limpio.replace('\n', ' ')
    texto_limpio = ' '.join(texto_limpio.split())
    texto_limpio = unidecode(texto_limpio.lower())
    return texto_limpio.strip()

def organize_result(r):
    if r is not None:
        return {
            "paperid": r.entry_id.split("/abs/")[1],
            "title": r.title,
            "updated": r.updated.isoformat(),
            "published": r.published.isoformat(),
            "summary": r.summary,
            "categories": r.categories,
            "authors": [aut.name for aut in r.authors]
        }
    else:
        return None

def obtain_result(client: arxiv.Client(), title: str):
    full_query = f"ti:{title.strip()}"
    #print(full_query)
    search = arxiv.Search(
        query = full_query,
        max_results = 1
        )

    result = client.results(search)

    try:
        r = next(result)
    except StopIteration:
        r = None

    if r is not None:
        if normalize(r.title) == normalize(title):
            return r
        else:
            return None

def arxiv_entry_mapper(data_entries):
    client = arxiv.Client()
    resultados_json = []
    for data_entry in data_entries:
        res = obtain_result(client, data_entry['title'])
        if res is not None:
            resultados_json.append(organize_result(res))
    return resultados_json

initial_extraction('data/dict_split_3.json', 'data/extraction/arxiv_visited.txt',
                       'data/extraction/arxiv_results.json', entry_mapper=arxiv_entry_mapper)