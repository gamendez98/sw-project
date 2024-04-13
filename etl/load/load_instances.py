from time import strptime
from urllib.parse import quote_plus

from rdflib import Graph, Namespace, Literal, BNode
from rdflib.namespace import RDF, RDFS, XSD
from numpy import nan

# %%
import pandas as pd

df = pd.read_hdf('semantic_web.h5', key='sw')

# %%

g = Graph()
BASE = Namespace('http://example.org/')
VOCAB = Namespace('http://example.org/vocab/')
g.bind('ex', BASE)
g.bind('exv', VOCAB)
invalid_values = [None, "", nan, [], {}]


# %%

def text_to_node(text):
    return BASE.term(quote_plus(text))


# %%

def connect_publications(graph, publication, row, connection_type):
    if connection_type == 'references':
        connection, inverse = (VOCAB.references, VOCAB.cites)
    else:
        connection, inverse = (VOCAB.cites, VOCAB.references)
    if row[connection_type] not in invalid_values:
        for connected_publication_info in row[connection_type]:
            connected_publication = text_to_node(connected_publication_info['paperId'])
            graph.add((connected_publication, RDF.type, VOCAB.Publication))
            graph.add((connected_publication, VOCAB.hasSemanticId, Literal(connected_publication_info['paperId'])))
            graph.add((publication, connection, connected_publication))
            graph.add((connected_publication, inverse, publication))


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
        if row[field] not in invalid_values:
            graph.add((publication, VOCAB.term(property), Literal(row[field])))
    # relationships between publications
    connect_publications(graph, publication, row, 'references')
    connect_publications(graph, publication, row, 'citations')
    # venue
    if row.venue not in invalid_values:
        venue = text_to_node(row.venue.lower())
        graph.add((venue, RDF.type, VOCAB.Venue))
        graph.add((publication, VOCAB.belongsToVenue, venue))
    # categories
    if row.category_string not in invalid_values:
        for category_string in row.categories:
            category = text_to_node(category_string.lower())
            graph.add((category, RDF.type, VOCAB.Category))
            graph.add((publication, VOCAB.belongsToCategory, category))
    # fields of study
    if row.fieldsOfStudy not in invalid_values:
        for field_of_study_string in row.fieldsOfStudy:
            field_of_study = text_to_node(field_of_study_string.lower())
            graph.add((field_of_study, RDF.type, VOCAB.FieldsOfStudy))
            graph.add((publication, VOCAB.belongsToFieldsOfStudy, field_of_study))
    # publication date
    if row.hasPublicationDate not in invalid_values:
        publication_date = strptime(row.hasPublicationDate, '%Y-%m-%d')
        graph.add((publication, VOCAB.hasPublicationDate, Literal(publication_date)))
    # updated on
    if row.updated not in invalid_values:
        updated_date = strptime(row.hasPublicationDate, '%Y-%m-%dT%H:%M:%S%z')
        graph.add((publication, VOCAB.hasPublicationDate, Literal(updated_date)))
    # sections
    if row.sections not in invalid_values:
        for section_title, section_body in row.sections.items():
            section = BNode()
            graph.add((section, RDF.type, VOCAB.Section))
            graph.add((section, VOCAB.hasSectionTitle, Literal(section_title)))
            graph.add((section, VOCAB.hasSectionBody, Literal(section_body)))
