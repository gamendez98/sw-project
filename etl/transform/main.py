import subprocess

from etl.transform.xml_to_json import enrich_semantic, enrich_arxiv


def main_transform():
    # GROBID extraction
    # these two lines require an instance of grobid server to be run
    # using `docker run --rm --init --ulimit core=0 -p 8070:8070 grobid/grobid:0.8.0`
    # extract information from semantic scholar pdfs
    subprocess.run([
        'grobid_client', '--input', 'data/extraction/pdfs_semantic', '--output',
        'data/extraction/pdfs_semantic_grobid_out', '--n', '12', '--consolidate_header',
        '--consolidate_citations', '--include_raw_citations', '--include_raw_affiliations', 'processFulltextDocument'
    ])
    # extract information from arxiv pdfs
    subprocess.run([
        'grobid_client', '--input', 'data/extraction/pdfs_arxiv', '--output', 'data/extraction/pdfs_arxiv_grobid_out',
        '--n', '12', '--consolidate_header', '--consolidate_citations', '--include_raw_citations',
        '--include_raw_affiliations', 'processFulltextDocument'
    ])
    # join the information extracted in the previous steps
    enrich_semantic()
    enrich_arxiv()
    # this joins all the information provided previously into a single file
    subprocess.call("etl/transform/file_union.py", shell=True)

    return


if __name__ == "__main__":
    main_transform()
