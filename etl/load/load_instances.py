import json
from time import strptime
from urllib.parse import quote_plus

import owlrl
from pandas import Series
from rdflib import Graph, Namespace, Literal, BNode, URIRef
from rdflib.namespace import RDF
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


def load_publication_entry(graph: Graph, row: Series):
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
    for property_name, field in literal_properties:
        if is_valid(row[field]):
            graph.add((publication, VOCAB.term(property_name), Literal(row[field])))
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


def load_author_entry(graph: Graph, row: Series):
    # load paper
    author = text_to_node(row.authorId)
    graph.add((author, RDF.type, VOCAB.Author))
    graph.add((author, VOCAB.hasAuthorId, Literal(row.authorId)))
    literal_properties = [
        ('hasUrl', 'url'),
        ('hasName', 'name'),
        ('hasHomepage', 'homepage'),
        ('hasPaperCount', 'paperCount'),
        ('hasCitationCount', 'citationCount'),
        ('hasHIndex', 'hIndex'),
    ]
    # simple properties
    for property_name, field in literal_properties:
        if is_valid(row[field]):
            graph.add((author, VOCAB.term(property_name), Literal(row[field])))
    if is_valid(row.externalIds):
        for external_id in row.externalIds:
            graph.add((author, VOCAB.hasExternalId, Literal(external_id)))
    if is_valid(row.aliases):
        for alias in row.aliases:
            graph.add((author, VOCAB.hasAlias, Literal(alias)))
    if is_valid(row.affiliations):
        for institution_name in row.affiliations:
            institution = text_to_node(institution_name)
            graph.add((institution, RDF.type, VOCAB.Institution))
            graph.add((author, VOCAB.affiliatedWith, Literal(institution)))


def load_topic_entry(graph: Graph, row: Series):
    if is_valid(row.semanticId):
        publication = text_to_node(row.semanticId)
        topics_info = eval(row.topics_babelify)
        for topic_info in topics_info:
            topic_uri = URIRef(topic_info.get('DBpediaURL'))
            graph.add((topic_uri, RDF.type, VOCAB.Topic))
            graph.add((publication, VOCAB.belongToTopic, topic_uri))
            graph.add((topic_uri, VOCAB.hasPublication, publication))
        topics_info = eval(row.topics_textrazor)
        for topic_info in topics_info:
            wiki_id = topic_info.get('topic_wikidata_id')
            topic_uri = URIRef(f'https://www.wikidata.org/wiki/{wiki_id}')
            graph.add((topic_uri, RDF.type, VOCAB.Topic))
            graph.add((publication, VOCAB.belongToTopic, topic_uri))
            graph.add((topic_uri, VOCAB.hasPublication, publication))


def create_graph():
    invalid_chars = [0x12, 0x13, 0x14, 0x17, 0xe, 0xf]
    df: pd.DataFrame = pd.read_hdf('data/transform/semantic_web_project_data.h5', key='sw')
    graph = Graph()
    graph.bind('ex', BASE)
    graph.bind('exv', VOCAB)
    graph.parse('schema.ttl', format='ttl')
    for _, row in tqdm(df.iterrows(), total=len(df)):
        load_publication_entry(graph, row)
    authors = pd.DataFrame([json.loads(l) for l in open('data/extraction/semantic_scholar_authors.json').readlines()])
    authors.drop_duplicates(subset=['authorId'], inplace=True)
    for _, row in tqdm(authors.iterrows(), total=len(authors)):
        load_author_entry(graph, row)
    topics = pd.read_csv('data/topics_data.csv')
    for _, row in tqdm(topics.iterrows(), total=len(topics)):
        load_topic_entry(graph, row)
    print('reasoning...')
    owl_reasoner = owlrl.CombinedClosure.RDFS_OWLRL_Semantics(graph, False, False, False)
    owl_reasoner.closure()
    owl_reasoner.flush_stored_triples()
    print('writing to file...')
    with open('project-schema.rdf', 'w') as f:
        file_content = graph.serialize(format='xml')
        file_content = "".join(c for c in file_content if ord(c) not in invalid_chars)
        f.write(file_content)


# %%

if __name__ == '__main__':
    create_graph()
