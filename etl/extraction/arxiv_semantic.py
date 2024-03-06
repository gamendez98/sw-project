import json

from etl.extraction.semantic_scholar import semantic_scholar_batch_details
from etl.extraction.utils import checkpoint_extraction


def details_from_arxiv():
    def semantic_from_arxiv_loader(input_path: str):
        with open(input_path, 'r') as input_file:
            for line in input_file.readlines():
                paper = json.loads(line)
                yield paper['paperid'], paper

    def semantic_from_arxiv_mapper(data_entries):
        ids = [f"ARXIV:{entry['paperid'][:-2]}" for entry in data_entries]
        return semantic_scholar_batch_details(ids)

    n = 4464
    checkpoint_extraction(
        input_file_path='data/extraction/arxiv_no_complete.json',
        visited_keys_path='data/extraction/arxiv_semantic_details.txt',
        output_path='data/extraction/arxiv_semantic_details_results.json',
        entry_mapper=semantic_from_arxiv_mapper,
        input_loader=semantic_from_arxiv_loader,
        input_size=n,
        batch_size=100
    )
