from pyshacl import validate
from rdflib import Graph, Namespace, Literal, BNode, URIRef, XSD, BNode
from rdflib.namespace import RDF, SH
from urllib.parse import quote_plus
from typing import List

# Definiendo nuestros namespaces
BASE = Namespace('http://example.org/')
VOCAB = Namespace('http://example.org/vocab/#')
INVALID_VALUES = [None, "", [], {}]

# Función para crear una URI
def text_to_node(text):
    return BASE.term(quote_plus(text))

# Añadir los datos nuevos al esquema
def add_data_to_graph(title: str, date: str, authors: List[str]):
    graph = Graph()
    graph.parse('schema.ttl', format='ttl')
    
    id_ = title + '-' + date
    pub = text_to_node(title)
    graph.add((pub, RDF.type, VOCAB.Publication))
    graph.add((pub, VOCAB.hasSemanticId, Literal(id_)))
    graph.add((pub, VOCAB.hasTitle, Literal(title)))
    graph.add((pub, VOCAB.publishedOnYear, Literal(int(date))))
    
    for a in authors:
        auth = text_to_node(a)
        graph.add((auth, RDF.type, VOCAB.Author))
        graph.add((auth, VOCAB.hasAlias, Literal(a)))
        graph.add((auth, VOCAB.wrote, pub))
        graph.add((pub, VOCAB.authoredBy, auth))

    return graph

# Creación del grafo de SHACL
def create_shacl_graph():
    g = Graph()
    g.bind('ex', BASE)
    g.bind('exv', VOCAB)
    g.bind("sh", SH)
    g.bind("xsd", XSD)
    
    # Crear un nodo shape para Publication
    publication_shape = VOCAB.PublicationShape
    g.add((publication_shape, RDF.type, SH.NodeShape))
    g.add((publication_shape, SH.nodeKind, SH.IRI))
    g.add((publication_shape, SH.targetClass, VOCAB.Publication))
    
    # Añadir restricciones para hasSemanticId
    has_semantic_id_property = BNode()
    g.add((publication_shape, SH.property, has_semantic_id_property))
    g.add((has_semantic_id_property, SH.path, VOCAB.hasSemanticId))
    g.add((has_semantic_id_property, SH.datatype, XSD.string))
    g.add((has_semantic_id_property, SH.minCount, Literal(1, datatype=XSD.integer)))
    g.add((has_semantic_id_property, SH.maxCount, Literal(1, datatype=XSD.integer)))
    g.add((has_semantic_id_property, SH.maxLength, Literal(200, datatype=XSD.integer)))
    g.add((has_semantic_id_property, SH.minLength, Literal(10, datatype=XSD.integer)))
    
    # Añadir restricciones para hasTitle
    has_title_property = BNode()
    g.add((publication_shape, SH.property, has_title_property))
    g.add((has_title_property, SH.path, VOCAB.hasTitle))
    g.add((has_title_property, SH.datatype, XSD.string))
    g.add((has_title_property, SH.minCount, Literal(1, datatype=XSD.integer)))
    g.add((has_title_property, SH.maxCount, Literal(1, datatype=XSD.integer)))
    g.add((has_title_property, SH.maxLength, Literal(200, datatype=XSD.integer)))
    
    # Añadir restricciones para publishedOnYear
    publication_date_property = BNode()
    g.add((publication_shape, SH.property, publication_date_property))
    g.add((publication_date_property, SH.path, VOCAB.publishedOnYear))
    g.add((publication_date_property, SH.datatype, XSD.integer))
    g.add((publication_date_property, SH.minCount, Literal(1, datatype=XSD.integer)))
    g.add((publication_date_property, SH.maxCount, Literal(1, datatype=XSD.integer)))
    g.add((publication_date_property, SH.maxInclusive, Literal(2024, datatype=XSD.integer)))
    g.add((publication_date_property, SH.minInclusive, Literal(1800, datatype=XSD.integer)))

    # Añadir restricciones para authoredBy
    authored_by_property = BNode()
    g.add((publication_shape, SH.property, authored_by_property))
    g.add((authored_by_property, SH.path, VOCAB.authoredBy))
    g.add((authored_by_property, SH['class'], VOCAB.Author))
    g.add((authored_by_property, SH.minCount, Literal(1, datatype=XSD.integer)))
    
    # Crear un nodo shape para Author
    author_shape = VOCAB.AuthorShape
    g.add((author_shape, RDF.type, SH.NodeShape))
    g.add((author_shape, SH.nodeKind, SH.IRI))
    g.add((author_shape, SH.targetClass, VOCAB.Author))
    
    # Añadir restricciones para hasAlias
    has_alias_property = BNode()
    g.add((author_shape, SH.property, has_alias_property))
    g.add((has_alias_property, SH.path, VOCAB.hasAlias))
    g.add((has_alias_property, SH.datatype, XSD.string))
    g.add((has_alias_property, SH.minCount, Literal(1, datatype=XSD.integer)))
    g.add((has_alias_property, SH.maxCount, Literal(1, datatype=XSD.integer)))
    g.add((has_alias_property, SH.maxLength, Literal(50, datatype=XSD.integer)))
    
    # Añadir restricciones para wrote
    wrote_property = BNode()
    g.add((author_shape, SH.property, wrote_property))
    g.add((wrote_property, SH.path, VOCAB.wrote))
    g.add((wrote_property, SH['class'], VOCAB.Publication))

    return g

# Función principal para validar si los datos pueden entrar a la ontología
def validate_shacl(title: str, date: str, authors: List[str]):
    graph = add_data_to_graph(title, date, authors)
    g = create_shacl_graph()
    conforms, _, _ = validate(graph, shacl_graph=g, advanced=True, debug=False)
    return conforms

if __name__ == "__main__":
    title = "I am an example title"
    date = "2020"
    authors = ["Isa M", "Felipe F", "Gus Gus"]
    title_long = "I'm an absurdly long long title really" * 100
    print(validate_shacl(title, date, authors))
    print(validate_shacl(title_long, date, authors))
    