from etl.extraction.arxiv_extraction import arxiv_extraction
from etl.extraction.arxiv_semantic import details_from_arxiv
from etl.extraction.pdf_extraction import download_pdfs_semantic_data, download_pdfs_arxiv_data
from etl.extraction.semantic_scholar import initial_extraction_scholar, author_extraction_scholar, \
    semantic_dense_connected


def main_extraction():
    initial_extraction_scholar()
    author_extraction_scholar()
    semantic_dense_connected()
    arxiv_extraction()
    details_from_arxiv()
    # join detail
    # extract dense
    download_pdfs_semantic_data()
    download_pdfs_arxiv_data()


if __name__ == '__main__':
    main_extraction()
