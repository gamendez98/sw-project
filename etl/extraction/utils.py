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


def initial_extraction(input_file_path: str, visited_keys_path: str, output_path: str, entry_mapper: Callable):
    '''
    Initial data extraction. Write results and entries already visited from input file
    :param input_file_path: the source provided by the teacher
    :param visited_keys_path: stores the already visited entries
    :param output_path: results as a list of jsons to be read like
        `results = [json.loads(entry) for entry in f.readlines()]`
    :param entry_mapper: function that takes the data provided by the teacher and returns the data provided by the API
    :return: None
    '''
    with (open(input_file_path, 'r') as input_file,
          open(visited_keys_path, 'r') as visited_keys_file):
        visited_keys = {key.strip() for key in visited_keys_file.readlines()}
        initial_source = json.load(input_file)
    with (open(output_path, 'a') as output_file,
          open(visited_keys_path, 'a') as visited_keys_file):
        for key, data in tqdm(initial_source.items(), total=len(initial_source), desc='retrieving semantic scholar'):
            if key in visited_keys:
                continue
            result = entry_mapper(data)
            if result:
                output_file.write(json.dumps(result))
                output_file.write('\n')
            visited_keys_file.write(key)
            visited_keys_file.write('\n')
