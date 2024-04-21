from etl.extraction.arxiv_extraction import arxiv_extraction
from etl.extraction.arxiv_semantic import details_from_arxiv
from etl.extraction.pdf_extraction import download_pdfs_semantic_data, download_pdfs_arxiv_data
from etl.extraction.semantic_scholar import initial_extraction_scholar, author_extraction_scholar


def main_extraction():
    # reads from the file provided by the professor and extracts information from semantic-scholar
    initial_extraction_scholar()
    # gets the information for all authors present in the results of the previous step
    author_extraction_scholar()
    # reads from the file provided by the professor and extracts information from the arxiv api
    arxiv_extraction()
    # gets additional details from the arxiv api for the results of the previous step
    details_from_arxiv()
    # download pdfs from semantic-web
    download_pdfs_semantic_data()
    # downloads pdfs from arxiv
    download_pdfs_arxiv_data()


if __name__ == '__main__':
    main_extraction()
