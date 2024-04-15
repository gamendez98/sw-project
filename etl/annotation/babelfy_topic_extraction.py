import urllib.request
import urllib.parse
import json
import gzip
import pandas as pd

from io import BytesIO
from typing import Callable
from tqdm import tqdm

# %%
service_url = 'https://babelfy.io/v1/disambiguate'
lang = 'EN'
key = 'your_api_key_here'

# %%
def initial_extraction_input_loader(input_file_path: str, max_data: int = 990):
    data = pd.read_csv(input_file_path)

    if "topics_babelify" in data.columns:
        data = data[data["topics_babelify"].isna()].reset_index(drop = True)

    data = data[["semanticId","title","abstract"]].iloc[:max_data]
    data = data.fillna("")
    for k, title, abstract in data.values:
        yield k, title, abstract

def babelify_mapper(keys, titles, abstracts):

    full_texts = [f"{title}\n{abstract}" for title, abstract in zip(titles, abstracts)]
    json_results = []

    for i in range(len(keys)):
        try:
            data_entry = full_texts[i]
            params = {
                'text': data_entry,
                'lang': lang,
                'key': key
            }

            # I just enjoy prints
            print(titles[i])

            url = service_url + '?' + urllib.parse.urlencode(params)
            request = urllib.request.Request(url)
            request.add_header('Accept-encoding', 'gzip')
            response = urllib.request.urlopen(request)

            if response.code == 200:
                if response.info().get('Content-Encoding') == 'gzip':
                    buf = BytesIO(response.read())
                    with gzip.GzipFile(fileobj=buf) as f:
                        response_data = json.loads(f.read().decode('utf-8'))
            
                        json_results.append({
                            "semanticId": keys[i],
                            "topics_babelify": response_data
                        })
        except:
            data_entry = full_texts[i][:500]
            params = {
                'text': data_entry,
                'lang': lang,
                'key': key
            }

            # I just enjoy prints
            print(titles[i])

            url = service_url + '?' + urllib.parse.urlencode(params)
            request = urllib.request.Request(url)
            request.add_header('Accept-encoding', 'gzip')
            response = urllib.request.urlopen(request)

            if response.code == 200:
                if response.info().get('Content-Encoding') == 'gzip':
                    buf = BytesIO(response.read())
                    with gzip.GzipFile(fileobj=buf) as f:
                        response_data = json.loads(f.read().decode('utf-8'))
            
                        json_results.append({
                            "semanticId": keys[i],
                            "topics_babelify": response_data
                        })

    return json_results

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

def checkpoint_extraction(input_file_path: str, visited_keys_path: str, output_path: str, entry_mapper: Callable, input_loader: Callable, batch_size: int = 30):

    def save_results(rs, ks, out, visited):
        for result in rs:
            if result:
                out.write(json.dumps(result))
                out.write('\n')
        for k in ks:
            visited.write(k)
            visited.write('\n')

    with open(visited_keys_path, 'r') as visited_keys_file:
        visited_keys = {key.strip() for key in visited_keys_file.readlines()}

    input_generator = input_loader(input_file_path)

    with (open(output_path, 'a') as output_file,
          open(visited_keys_path, 'a') as visited_keys_file):
        batches = batched(input_generator, n=batch_size, skip=(lambda x: x[0] in visited_keys))
        for batch in tqdm(batches, desc='retrieving topics'):
            keys = [k for k, _, _ in batch]
            titles = [t for _, t, _ in batch]
            abstracts = [a for _, _, a in batch]
            results = entry_mapper(keys, titles, abstracts)
            keys_with_valid_response = [x["semanticId"] for x in results]
            save_results(results, keys_with_valid_response, output_file, visited_keys_file)

def organize_data(input_file_path: str, topic_results_file_path: str):
    topic_results = []
    with open(topic_results_file_path, "r", encoding="utf-8") as input_file:
        for row in input_file:
            topic_results.append(json.loads(row))

    data = data = pd.read_csv(input_file_path)
    if "topics_babelify" in data.columns:
        data = data.drop("topics_babelify", axis = 1)

    topic_data = pd.DataFrame(topic_results)
    final_data = pd.merge(data, topic_data, on = "semanticId", how = "left")
    final_data.to_csv(input_file_path, index = False)

def main():
    checkpoint_extraction(
        input_file_path = "data/semantic_web_project_data.csv",
        visited_keys_path = "data/babelify_visited.txt",
        output_path = "data/babelify_topics.json",
        entry_mapper = babelify_mapper,
        input_loader = initial_extraction_input_loader
    )
    organize_data(
        input_file_path = "data/semantic_web_project_data.csv",
        topic_results_file_path = "data/babelify_topics.json"
    )

if __name__ == '__main__':
    main()