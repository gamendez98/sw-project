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
                cond1 = 'fig' not in section and 'lemma' not in section and 'proposition' not in section
                cond2 = 'theorem' not in section and 'corollary' not in section and 'table' not in section
                cond3 = 'case' not in section and 'example' not in section
                cond4 = bool(pattern.search(section))
                if cond1 and cond2 and cond3 and cond4:
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

    xml_data = extract_terms_from_xml('data/extraction/pdfs_semantic_grobid_out')

    semantic_data = {entry['paperId']: entry for entry in semantic_data}
    xml_data = {entry['paperId']: entry for entry in xml_data}

    join_data = [{**entry, **xml_data[paper_id]} for paper_id, entry in semantic_data.items()]

    file_path = 'semantic_xml_final_info.json'

    with open(file_path, 'w') as json_file:
        for i, json_obj in enumerate(join_data):
            json_str = json.dumps(json_obj)
            json_file.write(json_str)
            if i != len(join_data) - 1:
                json_file.write('\n')
