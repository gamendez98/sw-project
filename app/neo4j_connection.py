from neo4j import GraphDatabase
from thefuzz import process

URI = "neo4j://localhost:7687/"
AUTH = ("neo4j", "neo4j")
driver = GraphDatabase.driver(URI, auth=AUTH)


# Utility functions
def run_query(query, parameters=None):
    with driver.session() as session:
        result = session.run(query, parameters)
        records = [record for record in result]
        return records


def get_all_authors():
    query = "MATCH (n:ns0__Author) RETURN n.ns0__hasAlias AS alias"
    authors = run_query(query)
    return [record['alias'] for record in authors]

def search_author_fuzzy(author_name):
    all_authors = get_all_authors()
    best_matches = process.extract(author_name, all_authors, limit=5)
    return [match[0] for match in best_matches]


def search_publication_by_author_alias(name: str):
    query_author = """
    MATCH (n:ns0__Author)-[r:ns0__wrote]->(i:ns0__Publication)
    WHERE n.ns0__hasAlias = $author
    RETURN n.ns0__hasAlias AS alias,i.uri as publicationUri, i.ns0__hasTitle AS title, i.ns0__hasPdfPath as path
    """
    fuzzy_matches = search_author_fuzzy(name)
    results = []
    for match in fuzzy_matches:
        parameters = {"author": match}
        result = run_query(query_author, parameters)
        if result:
            results.extend(result)
    results_dict = [dict(r) for r in results]
    return results_dict

def search_publications_by_topic(topic_uri: str):
    query_topic = """
    MATCH (n:ns0__Topic)-[r:ns0__hasPublication]->(i:ns0__Publication)
    WHERE n.uri =~ $topic
    RETURN n.uri as uri,i.uri as publicationUri, i.ns0__hasTitle AS title, i.ns0__hasPdfPath as path
    """
    parameters = {"topic": f'.*{topic_uri}.*'}
    result = run_query(query_topic, parameters)
    results_dict = [dict(r) for r in result]
    return results_dict


def search_publications_by_field_of_study(field_of_study_uri: str):
    query_field_of_study = """
    MATCH (n:ns0__Publication)-[r:ns0__belongsToFieldsOfStudy]->(a:ns0__FieldsOfStudy)
    WHERE a.uri =~ $field
    RETURN a.uri as field_uri, n.uri as publicationUri,n.ns0__hasTitle AS title, n.ns0__hasPdfPath as path
    """
    parameters = {"field": f'.*{field_of_study_uri}.*'}
    result = run_query(query_field_of_study, parameters)
    results_dict = [dict(r) for r in result]
    return results_dict


def suggest_related_publications(paper_uri):
    query_paper_recommendation = """
    MATCH (n:ns0__Publication)-[r:ns0__belongToTopic]->(a:ns0__Topic) 
    WHERE n.uri = $paper_uri

    // Randomize the order and select 3 topics
    WITH a.uri AS topicUri, n.ns0__hasTitle AS title, rand() AS randomOrder
    ORDER BY randomOrder
    LIMIT 3

    // Fetch other papers associated with these randomly selected topics
    MATCH (otherPapers:ns0__Publication)-[:ns0__belongToTopic]->(relatedTopics:ns0__Topic)
    WHERE relatedTopics.uri = topicUri
    RETURN title, topicUri, otherPapers.uri as publicationUri,otherPapers.ns0__hasTitle AS relatedPaperTitle,
    otherPapers.ns0__hasPdfPath as path
    """
    parameters = {"paper_uri": paper_uri}
    result = run_query(query_paper_recommendation, parameters)
    results_dict = [dict(r) for r in result]
    return results_dict

def search_paper_references(publication_uri: str):
    query_topic = """
        MATCH (m:ns0__Publication)-[r:ns0__references]->(n:ns0__Publication) 
        WHERE m.uri = $publication_uri
        RETURN n.uri as publicationUri, n.ns0__hasTitle as title, n.ns0__hasReferenceCount as referenceCount ,
        n.ns0__hasCitationCount as citationCount, n.ns0__hasInfluentialCitationCount as influentialCount,
        n.ns0__hasPublicationDate as publicationDate, n.ns0__hasAbstract as abstract
    """
    parameters = {"publication_uri": f'{publication_uri}'}
    result = run_query(query_topic, parameters)
    results_dict = [dict(r) for r in result]
    return results_dict


def search_paper_details(publication_uri: str):
    query_topic = """
        MATCH (n:ns0__Publication)
        WHERE n.uri = $publication_uri 
        RETURN n.ns0__hasTitle as title, n.ns0__hasReferenceCount as referenceCount ,
        n.ns0__hasCitationCount as citationCount, n.ns0__hasInfluentialCitationCount as influentialCount,
        n.ns0__hasPublicationDate as publicationDate,n.ns0__hasPdfPath as path ,n.ns0__hasAbstract as abstract
    """
    parameters = {"publication_uri": f'{publication_uri}'}
    result = run_query(query_topic, parameters)
    results_dict = [dict(r) for r in result]
    return results_dict

def create_publication(title, date):
    id = title + '-' + date
    query = """CREATE (paper:ns0__Publication {ns0__hasSemanticId: $id, 
                ns0__hasTitle: $title, ns0__publishedOnYear: $date, uri: $uri})
            RETURN paper"""
    parameters = {"id": id, "title": title, "date": date, "uri": id}
    return run_query(query, parameters)

def create_author(name, date):
    query = """CREATE (new:ns0_Author {ns0__hasAlias: $name, uri: $uri}) RETURN new"""
    uri = name + date
    parameters = {"name": name, "uri": uri}
    return run_query(query, parameters)

def get_author(name):
    query = "MATCH (n:ns0_Author) WHERE n.ns0hasAlias = $name RETURN n.ns0_hasAlias AS alias"
    parameters = {"name": name}
    value = run_query(query, parameters)
    return value

def create_paper_authors(authors, title, date):
    create_p = create_publication(title, date)

    if len(create_p) == 0:
        return []

    query = """
        MATCH (n:ns0__Publication)
        WHERE n.ns0__hasTitle = $title
        CREATE (test:ns0__Author {ns0__hasAlias: $name})-[:ns0__wrote]->(n)
        RETURN test
    """

    query2 = """
        MATCH (n:ns0__Publication)
        WHERE n.ns0__hasTitle = $title
        CREATE (n)-[:ns0__authoredBy]->(test:ns0__Author {ns0__hasAlias: $name})
        RETURN test
    """

    for a in authors:
        status = get_author(a)
        if len(status) == 0:
            create_a = create_author(a, date)
            if len(create_a) == 0:
                return []
        parameters = {"name": a, "title": title}
        create_p_a = run_query(query, parameters)
        create_p_by = run_query(query2, parameters)
        if len(create_p_a) == 0 or len(create_p_by) == 0:
            return []
    
    return "Creación exitosa :D"


def get_all_papers():
    query = "MATCH (n:ns0_Publication) RETURN n.ns0__hasTitle AS title"
    authors = run_query(query)
    return [record['title'] for record in authors]

def search_paper_fuzzy(paper_title):
    all_papers = get_all_papers()
    best_matches = process.extract(paper_title, all_papers, limit=5)
    return [match[0] for match in best_matches]

def search_paper_info(paper_title: str, do_fuzzy: int):
    query_paper = """
    MATCH (n:ns0__Publication)
    WHERE n.ns0__hasTitle = $paper_title
    OPTIONAL MATCH (n)-[:ns0__authoredBy]->(a:ns0__Author)
    OPTIONAL MATCH (n)-[:ns0__belongToTopic]->(t:ns0__Topic)
    OPTIONAL MATCH (n)-[:ns0__belongsToCategory]->(c:ns0__Category)
    OPTIONAL MATCH (n)-[:ns0__belongsToFieldsOfStudy]->(f:ns0__FieldsOfStudy)
    RETURN n.ns0__hasSemanticId as semantic_id,
        n.ns0__hasTitle as title, 
        n.ns0__hasReferenceCount as reference_count, 
        n.ns0__hasCitationCount as citation_count, 
        n.ns0__hasPublicationDate as publication_date, 
        n.ns0__hasAbstract as abstract,
        n.ns0__hasPdfPath as path,
        COLLECT(DISTINCT a.ns0__hasAlias) as authors,
        COLLECT(DISTINCT t.uri) as topics,
        COLLECT(DISTINCT c.uri) as categories,
        COLLECT(DISTINCT f.uri) as fields_of_study
    """
    if do_fuzzy:
        fuzzy_matches = search_paper_fuzzy(paper_title)
        results = []
        for match in fuzzy_matches:
            parameters = {"paper_title": match}
            result = run_query(query_paper, parameters)
            if result:
                results.extend(result)
    else:
        parameters = {"paper_title": paper_title}
        results = run_query(query_paper, parameters)
    results_dict = [dict(r) for r in results]
    return results_dict
    

