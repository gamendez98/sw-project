import json

import requests

from etl.extraction.utils import checkpoint_extraction


def download_file(url, destination):
    try:
        # Make a GET request to the URL
        response = requests.get(url)

        if response.status_code == 200:
            # Open the file in binary mode and write the downloaded content
            with open(destination, 'wb') as file:
                file.write(response.content)
        else:
            print(f"Error downloading the file. Status code: {response.status_code}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


# %%

def download_pdfs_semantic_data():
    n = 4129

    def semantic_scholar_loader(input_path: str):
        with open(input_path, 'r') as input_file:
            for line in input_file.readlines():
                paper = json.loads(line)
                yield paper['paperId'], paper

    def download_mapper(data_entries):
        results = []
        for entry in data_entries:
            pdf_url = entry['openAccessPdf'] or {}
            pdf_url = pdf_url.get('url')
            arxiv_id = entry['externalIds'].get('ArXiv')
            url = pdf_url or (
                f'https://arxiv.org/pdf/{arxiv_id}' if arxiv_id else None
            )
            if url:
                download_file(url, f'data/extraction/pdfs_semantic/{entry["paperId"]}.pdf')
            source = None
            if pdf_url:
                source = 'semantic'
            elif arxiv_id:
                source = 'arxiv'
            results.append({
                'paperId': entry['paperId'],
                'source': source
            })
        return results

    checkpoint_extraction(
        input_file_path='data/extraction/semantic_dense_connected.json',
        visited_keys_path='data/extraction/visited_papers_dense_download.txt',
        output_path='data/extraction/semantic_dense_download.json',
        entry_mapper=download_mapper,
        input_loader=semantic_scholar_loader,
        input_size=n,
        batch_size=1
    )


def download_pdfs_arxiv_data():
    n = 3984

    def download_mapper(data_entries):
        results = []
        for entry in data_entries:
            url = f'https://arxiv.org/pdf/{entry["paperid"][:-2]}'
            download_file(url, f'data/extraction/pdfs_arxiv/{entry["paperid"].replace("/", "_")}.pdf')
            results.append({
                'paperid': entry['paperid']
            })
        return results

    def download_loader(input_path: str):
        with open(input_path, 'r') as input_file:
            for line in input_file.readlines():
                paper = json.loads(line)
                yield paper['paperid'], paper

    checkpoint_extraction(
        input_file_path='data/extraction/arxiv_results.json',
        visited_keys_path='data/extraction/visited_arxiv_download.txt',
        output_path='data/extraction/arxiv_download.json',
        entry_mapper=download_mapper,
        input_loader=download_loader,
        input_size=n,
        batch_size=1
    )


# %%

if __name__ == '__main__':
    download_pdfs()
