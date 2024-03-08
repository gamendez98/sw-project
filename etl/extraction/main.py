from etl.extraction.arxiv_extraction import arxiv_extraction
from etl.extraction.arxiv_semantic import details_from_arxiv
from etl.extraction.pdf_extraction import download_pdfs_semantic_data, download_pdfs_arxiv_data
from etl.extraction.semantic_scholar import initial_extraction_scholar, author_extraction_scholar


def main_extraction():
    initial_extraction_scholar()
    author_extraction_scholar()
    arxiv_extraction()
    details_from_arxiv()
    download_pdfs_semantic_data()
    download_pdfs_arxiv_data()


if __name__ == '__main__':
    main_extraction()
