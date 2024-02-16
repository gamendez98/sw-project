import json
import random
import time
from typing import Callable

from tqdm import tqdm


def retry(max_retries=7, base_delay=2.5, valid_codes=(200, 404)):
    def decorator(f):
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                results = f(*args, **kwargs)
                if results.status_code in valid_codes:
                    return results
                delay = base_delay * 2 ** retries + random.uniform(0, 1)
                print('retry {} times, delay {}'.format(retries, delay))
                time.sleep(delay)
                retries += 1
            results = f(*args, **kwargs)
            if results.status_code in valid_codes:
                return results
            raise ValueError("Too many retries, lets just crash this")

        return wrapper

    return decorator


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


def initial_extraction(input_file_path: str, visited_keys_path: str, output_path: str, entry_mapper: Callable,
                       batch_size: int = 30):
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
    with (open(output_path, 'a') as output_file,
          open(visited_keys_path, 'a') as visited_keys_file):
        batches = batched(initial_source.items(), n=batch_size, skip=(lambda x: x[0] in visited_keys))
        for batch in tqdm(batches, total=int((len(initial_source) - len(visited_keys)) / batch_size),
                          desc='retrieving semantic scholar'):
            keys = [k for k, _ in batch]
            datums = [d for _, d in batch]
            results = entry_mapper(datums)
            save_results(results, keys, output_file, visited_keys_file)
