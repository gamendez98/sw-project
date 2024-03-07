import os
from typing import List

from tqdm import tqdm
from bs4 import BeautifulSoup
import re
import json


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
        if '.txt' not in file_name:
            new_entry = dict()
            new_entry['paperId'] = file_name.replace(".grobid.tei.xml", "")
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
                    if keywords != None and len(keywords) > 0:
                        new_entry['keywords'] = keywords
                except:
                    no_keywords.append(id)

            new_entry['pdfPath'] = path
            data_json.append(new_entry)

    return data_json


# %%

def enrich_semantic():
    with open('data/extraction/semantic_scholar_results.json', 'r') as f:
        semantic_data = [json.loads(line) for line in f]

    xml_data = extract_terms_from_xml('data/transform/pdfs_semantic_grobid_out')

    semantic_data = {entry['paperId']: entry for entry in semantic_data}
    xml_data = {entry['paperId']: entry for entry in xml_data}

    join_data = [{**entry, **xml_data[paper_id]} for paper_id, entry in semantic_data.items()]

    file_path = 'data/transform/semantic_xml_final_info.json'

    with open(file_path, 'w') as json_file:
        for i, json_obj in enumerate(join_data):
            json_str = json.dumps(json_obj)
            json_file.write(json_str)
            if i != len(join_data) - 1:
                json_file.write('\n')
