import arxiv, re
from unidecode import unidecode

from etl.extraction.utils import initial_extraction_input_loader, checkpoint_extraction


def normalize(texto: str) -> str:
    texto_limpio = re.sub(r'\d+\.\d+-\d+\.\d+\|', '', texto)
    texto_limpio = re.sub(r'[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ ]', '', texto_limpio)
    texto_limpio = texto_limpio.replace('\n', ' ')
    texto_limpio = ' '.join(texto_limpio.split())
    texto_limpio = unidecode(texto_limpio.lower())
    return texto_limpio.strip()


def organize_result(result):
    if result is not None:
        return {
            "paperid": result.entry_id.split("/abs/")[1],
            "title": result.title,
            "updated": result.updated.isoformat(),
            "published": result.published.isoformat(),
            "summary": result.summary,
            "categories": result.categories,
            "authors": [aut.name for aut in result.authors]
        }
    else:
        return None


def obtain_result(client: arxiv.Client(), title: str):
    full_query = f"ti:{title.strip()}"
    search = arxiv.Search(
        query=full_query,
        max_results=1
    )

    result = client.results(search)

    result = next(result, None)
    if result is not None:
        if normalize(result.title) == normalize(title):
            return result


def arxiv_entry_mapper(data_entries):
    client = arxiv.Client()
    resultados_json = []
    for data_entry in data_entries:
        res = obtain_result(client, data_entry['title'])
        if res is not None:
            resultados_json.append(organize_result(res))
    return resultados_json


def arxiv_extraction():
    checkpoint_extraction(
        input_file_path='data/dict_split_3.json',
        visited_keys_path='data/extraction/arxiv_visited.txt',
        output_path='data/extraction/arxiv_results.json',
        entry_mapper=arxiv_entry_mapper,
        input_loader=initial_extraction_input_loader,
        input_size=156239
    )
