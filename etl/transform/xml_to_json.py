import os
from typing import List

from tqdm import tqdm
from bs4 import BeautifulSoup
import re
import json

from etl.transform.utils import join_data


def extract_terms_from_keywords(xml_file_path: str) -> List[str]:
    with open(xml_file_path, 'r') as xml_file:
        xml_data = xml_file.read()
        pattern = r'<keywords>(.*?)</keywords>'
        match = re.search(pattern, xml_data, re.DOTALL)

        if match:
            keywords_section = match.group(1).strip()
            term_pattern = r'<term>(.*?)</term>'
            term_matches = re.findall(term_pattern, keywords_section)

            return term_matches
        else:
            return []


# %%

def extract_terms_from_xml(xml_folder_path: str) -> List[dict]:
    file_names = os.listdir(path=xml_folder_path)

    data_json = []
    no_keywords = []
    pattern = re.compile(r'^[a-zA-Z0-9]+$')
    unwanted_tags = ['theorem', 'corollary', 'table', 'fig', 'lemma', 'proposition', 'case', 'example']

    for file_name in tqdm(file_names):
        if '.txt' in file_name:
            continue
        new_entry = {'paperId': file_name.replace(".grobid.tei.xml", "")}
        path = os.path.join(xml_folder_path, file_name)
        with open(path, 'r', encoding="utf-8") as file:
            data = file.read()
        soup = BeautifulSoup(data, 'xml')
        elements = soup.find_all('head')
        for element in elements:
            section = str(element.text.lower())
            has_unwanted_tag = any(unwanted_tag in section for unwanted_tag in unwanted_tags)
            if bool(pattern.search(section)) and not has_unwanted_tag:
                paragraph = element.find_next('p')
                if paragraph:
                    paragraph_text = paragraph.get_text(separator='')
                    new_entry[section] = paragraph_text
            try:
                keywords = extract_terms_from_keywords(path)
                if keywords is not None and len(keywords) > 0:
                    new_entry['keywords'] = keywords
            except:
                no_keywords.append(id)

        new_entry['pdfPath'] = path
        data_json.append(new_entry)

    return data_json


# %%


def write_joined_data(output_path, joined_data):
    with open(output_path, 'w') as json_file:
        for i, json_obj in enumerate(joined_data):
            json_str = json.dumps(json_obj)
            json_file.write(json_str)
            if i != len(joined_data) - 1:
                json_file.write('\n')


def enrich_data(input_path, xml_directory, output_path, id_field):
    with open(input_path, 'r') as f:
        semantic_data = [json.loads(line) for line in f]
    xml_data = extract_terms_from_xml(xml_directory)

    joined_data = join_data(semantic_data, xml_data, id_field, 'paperId')
    write_joined_data(output_path, joined_data)


def enrich_semantic():
    enrich_data(
        input_path='data/extraction/semantic_scholar_results.json',
        xml_directory='data/transform/pdfs_semantic_grobid_out',
        output_path='data/transform/semantic_xml_final_info.json',
        id_field='paperId'
    )


def enrich_arxiv():
    enrich_data(
        input_path='data/extraction/arxiv_results.json.json',
        xml_directory='data/transform/pdfs_arxiv_grobid_out',
        output_path='data/transform/semantic_xml_final_info.json',
        id_field='paperId'
    )
