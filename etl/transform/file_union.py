import json
import os
import pandas as pd
import numpy as np

from etl.extraction.pdf_extraction import download_file
from etl.extraction.utils import checkpoint_extraction


# %%

def some_all(data):
    f1 = set(data[0].keys())
    for entry in data[1:]:
        f1 |= set(entry.keys())

    f2 = set(data[0].keys())
    for entry in data[1:]:
        f2 |= set(entry.keys())

    return f1, f2


ARXIV_FIELDS = ['paperid', 'title', 'updated', 'published', 'summary', 'categories', 'authors']
SEMANTIC_FIELDS = ['paperId', 'title', 'venue', 'year', 'abstract', 'referenceCount', 'citationCount',
                   'influentialCitationCount', 'isOpenAccess', 'openAccessPdf', 'fieldsOfStudy', 'publicationTypes',
                   'publicationDate', 'journal', 'externalIds']
ALL_FIELDS = ARXIV_FIELDS + SEMANTIC_FIELDS

# %%
'''
other tables:
categories,
authors,
fieldsOfStudy,
references,
citations,
'''

# %%
q1_file = '/home/gustavo/Documents/sw-project/data/transform/arxiv_xml_final_info.json'
q2_file = 'data/extraction/semantic_arxiv_papers.json'
q3_file = 'data/extraction/semantic_dense_connected.json'
q4_file = 'data/extraction/semantic_scholar_results_link.json'

# %%

q_sdap1 = [json.loads(l) for l in open(q1_file).readlines()]
q_sda2 = [json.loads(l) for l in open(q2_file).readlines()]
q_sd3 = [json.loads(l) for l in open(q3_file).readlines()]
q_s4 = [json.loads(l) for l in open(q4_file).readlines()]


# %%

def df_from_sdap(sdap):
    fields = list({'abstract', 'citationCount', 'corpusId', 'categories', 'authors', 'fieldsOfStudy', 'references',
                   'citations',
                   'fieldsOfStudy', 'influentialCitationCount', 'isOpenAccess', 'journal', 'openAccessPdf', 'paperId',
                   'paperid', 'pdfPath', 'publicationDate', 'published', 'referenceCount',
                   'sections', 'semanticId', 'summary', 'title', 'updated', 'venue', 'year'})
    df = pd.DataFrame([
        [entry.get(f, None) for f in fields] for entry in sdap
    ], columns=fields)
    df['semanticId'] = df.semanticId.fillna(df.paperId)
    df.drop(columns=['paperId'], inplace=True)
    df.drop_duplicates(subset=['semanticId'], inplace=True)
    return df


df_sdap = df_from_sdap(q_sdap1)


# %%

def join_dicts(d1, d2, prefix1, prefix2):
    k1 = set(d1.keys())
    k2 = set(d2.keys())
    result = {}
    both = k1 & k2
    for i in both:
        result[prefix1 + i] = d1[i]
        result[prefix2 + i] = d2[i]
    for i in k1 - both:
        result[i] = d1[i]
    for i in k2 - both:
        result[i] = d2[i]

    return result


def flat_sda(sda):
    return [
        join_dicts(entry['semantic_scholar'], entry['arxiv_api'], 'semantic_', 'arxiv_') for entry in sda
    ]


def df_from_sda(sda):
    sda = flat_sda(sda)
    fields = list({'semantic_title', 'arxiv_title', 'paperId', 'venue', 'abstract', 'categories', 'authors',
                   'openAccessPdf', 'fieldsOfStudy', 'referenceCount', 'journal', 'corpusId',
                   'influentialCitationCount', 'citationCount', 'year', 'publicationDate',
                   'isOpenAccess', 'summary', 'updated', 'paperid', 'published'
                                                                    'categories', 'authors', 'fieldsOfStudy',
                   'references', 'citations', })
    df = pd.DataFrame([
        [entry.get(f, None) for f in fields] for entry in sda
    ], columns=fields)
    return df


df_sda = df_from_sda(q_sda2)
df_sda['title'] = df_sda['semantic_title']
df_sda.drop(columns=['semantic_title', 'arxiv_title'], inplace=True)

# %%

sdap_ids = set(df_sdap['semanticId'])

df_q12 = pd.concat([df_sdap, df_sda[~df_sda.paperId.isin(sdap_ids)]], ignore_index=True)
df_q12['semanticId'] = df_q12.semanticId.fillna(df_q12.paperId)
df_q12 = df_q12.drop(columns=['paperId', 'corpusId'])
df_q12.drop_duplicates(subset=['semanticId'], inplace=True)


# %%

def df_from_sd(sd):
    fields = list({'abstract', 'citationCount', 'corpusId', 'fieldsOfStudy',
                   'influentialCitationCount', 'isOpenAccess', 'journal', 'openAccessPdf', 'paperId', 'publicationDate',
                   'referenceCount', 'title', 'venue', 'year',
                   'categories', 'authors', 'fieldsOfStudy', 'references', 'citations', })
    df = pd.DataFrame([
        [entry.get(f, None) for f in fields] for entry in sd
    ], columns=fields)
    return df


df_sd = df_from_sd(q_sd3)
df_sd.rename(columns={'paperId': 'semanticId'}, inplace=True)


# %%
def clean_arxiv_id(text):
    return np.nan if pd.isna(text) else 'v'.join(text.split('v')[:-1])


q12_ids = set(df_q12['semanticId'])

df_q123 = pd.concat([df_q12, df_sd[~df_sd.semanticId.isin(q12_ids)]])
df_q123.drop_duplicates(subset=['semanticId'], inplace=True)
df_q123['arxivId'] = df_q123.paperid.apply(clean_arxiv_id)

# %%

arxiv_files = os.listdir('data/extraction/pdfs_arxiv')
semantic_files = os.listdir('data/extraction/pdfs_semantic')
# %%
arxiv_f_ids = [clean_arxiv_id(f.replace('_', '/')) for f in arxiv_files]
semantic_f_ids = [f[:-4] for f in semantic_files]

df_q123['has_file'] = df_q123.semanticId.isin(semantic_f_ids) | df_q123.arxivId.isin(arxiv_f_ids)

# %%

with open('data/extraction/semantic_new_download.json') as file:
    new_files = [json.loads(l) for l in file.readlines()]

new_files = [f for f in new_files if f['source']]
ids_with_papers = [entry['paperId'] for entry in new_files]

# %%

q_s4_files = [entry for entry in q_s4 if entry['paperId'] in ids_with_papers]
df_s = df_from_sd(q_s4_files)
df_s.rename(columns={'paperId': 'semanticId'}, inplace=True)
df_s['has_file'] = True

# %%

final_df = pd.concat([df_q123, df_s])
final_df.drop_duplicates(subset=['semanticId'], inplace=True)


def get_file_path(entry):
    semanticId = entry.semanticId
    arxivId = entry.arxivId
    if semanticId in semantic_f_ids:
        return f'data/extraction/pdfs_semantic/{semanticId}.pdf'
    if arxivId in arxiv_f_ids:
        return f'data/extraction/pdfs_arxiv/{semanticId}.pdf'
    return np.nan


def get_file_url(entry):
    pdf_url = entry['openAccessPdf'] or {}
    pdf_url = pdf_url.get('url')
    arxiv_id = entry.arxivId
    if pd.isna(arxiv_id):
        return None
    return pdf_url or (
        f'https://arxiv.org/pdf/{arxiv_id}' if arxiv_id else None
    )


final_df['pdfPath'] = final_df.apply(get_file_path, axis=1)
final_df['pdfUrl'] = final_df.apply(get_file_url, axis=1)
final_df.drop(columns=['has_file'], inplace=True)
final_df.drop(columns=['openAccessPdf'], inplace=True)
final_df['arxivId'] = final_df.arxivId.fillna(final_df.paperid)
final_df.drop(columns=['paperid'], inplace=True)
# %%

final_df.to_csv('semantic_we_project_data.csv')

# %%
