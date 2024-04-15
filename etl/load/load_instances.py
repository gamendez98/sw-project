from time import strptime
from urllib.parse import quote_plus

from rdflib import Graph, Namespace, Literal, BNode
from rdflib.namespace import RDF, RDFS, XSD
from numpy import isnan

# %%
import pandas as pd
from tqdm import tqdm

# %%

BASE = Namespace('http://example.org/')
VOCAB = Namespace('http://example.org/vocab/')
INVALID_VALUES = [None, "", [], {}]


# %%

def text_to_node(text):
    return BASE.term(quote_plus(text))


def is_valid(value):
    return not ((type(value) == float and isnan(value)) or value in INVALID_VALUES)


# %%

def connect_publications(graph, publication, row, connection_type):
    if connection_type == 'references':
        connection, inverse = (VOCAB.references, VOCAB.cites)
    else:
        connection, inverse = (VOCAB.cites, VOCAB.references)
    if is_valid(row[connection_type]):
        for connected_publication_info in row[connection_type]:
            paper_id = connected_publication_info.get('paperId')
            if paper_id:
                connected_publication = text_to_node(paper_id)
                graph.add((connected_publication, RDF.type, VOCAB.Publication))
                graph.add((connected_publication, VOCAB.hasSemanticId, Literal(paper_id)))
                graph.add((publication, connection, connected_publication))
                graph.add((connected_publication, inverse, publication))


def connect_authors(graph, publication, authors_info):
    if is_valid(authors_info):
        for author_info in authors_info:
            author_id = author_info.get('authorId')
            author_name = author_info.get('name')
            if author_id:
                author = text_to_node(author_id)
                graph.add((author, RDF.type, VOCAB.Author))
                graph.add((author, VOCAB.hasAuthorId, Literal(author_id)))
                graph.add((publication, VOCAB.authoredBy, author))
                graph.add((author, VOCAB.wrote, publication))
                if author_name:
                    graph.add((author, VOCAB.hasName, Literal(author_name)))


# %%


def load_publication_entry(graph: Graph, row):
    # load publication
    publication = text_to_node(row.semanticId)
    graph.add((publication, RDF.type, VOCAB.Publication))
    graph.add((publication, VOCAB.hasSemanticId, Literal(row.semanticId)))
    literal_properties = [
        ('hasCitationCount', 'citationCount'),
        ('hasTitle', 'title'),
        ('hasReferenceCount', 'referenceCount'),
        ('hasPdfPath', 'pdfPath'),
        ('hasAbstract', 'abstract'),
        ('isOpenAccess', 'isOpenAccess'),
        ('hasArxivId', 'arxivId'),
        ('hasCorpusId', 'corpusId'),
        ('hasInfluentialCitationCount', 'influentialCitationCount'),
        ('hasPdfUrl', 'pdfUrl'),
    ]
    # simple properties
    for property, field in literal_properties:
        if is_valid(row[field]):
            graph.add((publication, VOCAB.term(property), Literal(row[field])))
    # relationships between publications
    connect_publications(graph, publication, row, 'references')
    connect_publications(graph, publication, row, 'citations')
    # venue
    if is_valid(row.venue):
        venue = text_to_node(row.venue.lower())
        graph.add((venue, RDF.type, VOCAB.Venue))
        graph.add((publication, VOCAB.belongsToVenue, venue))
    # authors
    connect_authors(graph, publication, row.authors)
    # categories
    if is_valid(row.categories):
        for category_string in row.categories:
            category = text_to_node(category_string.lower())
            graph.add((category, RDF.type, VOCAB.Category))
            graph.add((publication, VOCAB.belongsToCategory, category))
    # fields of study
    if is_valid(row.fieldsOfStudy):
        for field_of_study_string in row.fieldsOfStudy:
            field_of_study = text_to_node(field_of_study_string.lower())
            graph.add((field_of_study, RDF.type, VOCAB.FieldsOfStudy))
            graph.add((publication, VOCAB.belongsToFieldsOfStudy, field_of_study))
    # publication date
    if is_valid(row.publicationDate):
        publication_date = strptime(row.publicationDate, '%Y-%m-%d')
        graph.add((publication, VOCAB.hasPublicationDate, Literal(publication_date)))
    # updated on
    if is_valid(row.updated):
        updated_date = strptime(row.updated, '%Y-%m-%dT%H:%M:%S%z')
        graph.add((publication, VOCAB.hasPublicationDate, Literal(updated_date)))
    # sections
    if is_valid(row.sections):
        for section_title, section_body in row.sections.items():
            section = BNode()
            graph.add((section, RDF.type, VOCAB.Section))
            graph.add((section, VOCAB.hasSectionTitle, Literal(section_title)))
            graph.add((section, VOCAB.hasSectionBody, Literal(section_body)))


def create_graph():
    df: pd.DataFrame = pd.read_hdf('data/transform/semantic_web_project_data.h5', key='sw')
    graph = Graph()
    graph.bind('ex', BASE)
    graph.bind('exv', VOCAB)
    graph.parse('schema.ttl', format='ttl')
    for _, row in tqdm(df.iterrows(), total=len(df)):
        load_publication_entry(graph, row)


if __name__ == '__main__':
    create_graph()
