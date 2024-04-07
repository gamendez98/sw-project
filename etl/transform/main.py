import subprocess

from etl.transform.xml_to_json import enrich_semantic, enrich_arxiv


def main_transform():
    # GROBID extraction
    # these two lines require an instance of grobid server to be run
    # using `docker run --rm --init --ulimit core=0 -p 8070:8070 grobid/grobid:0.8.0`
    subprocess.run([
        'grobid_client', '--input', 'data/extraction/pdfs_semantic', '--output',
        'data/extraction/pdfs_semantic_grobid_out', '--n', '12', '--consolidate_header',
        '--consolidate_citations', '--include_raw_citations', '--include_raw_affiliations', 'processFulltextDocument'
    ])
    subprocess.run([
        'grobid_client', '--input', 'data/extraction/pdfs_arxiv', '--output', 'data/extraction/pdfs_arxiv_grobid_out',
        '--n', '12', '--consolidate_header', '--consolidate_citations', '--include_raw_citations',
        '--include_raw_affiliations', 'processFulltextDocument'
    ])
    enrich_semantic()
    enrich_arxiv()

    return


if __name__ == "__main__":
    main_transform()
