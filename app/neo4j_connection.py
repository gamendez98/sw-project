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
    RETURN n.ns0__hasAlias AS alias, i.ns0__hasTitle AS title, i.ns0__hasPdfPath as path
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
    RETURN n.uri as uri, i.ns0__hasTitle AS title, i.ns0__hasPdfPath as path
    """
    parameters = {"topic": f'.*{topic_uri}.*'}
    result = run_query(query_topic, parameters)
    results_dict = [dict(r) for r in result]
    return results_dict


def search_publications_by_field_of_study(field_of_study_uri: str):
    query_field_of_study = """
    MATCH (n:ns0__Publication)-[r:ns0__belongsToFieldsOfStudy]->(a:ns0__FieldsOfStudy)
    WHERE a.uri =~ $field
    RETURN a.uri as field_uri, n.ns0__hasTitle AS title, n.ns0__hasPdfPath as path
    """
    parameters = {"field": f'.*{field_of_study_uri}.*'}
    result = run_query(query_field_of_study, parameters)
    results_dict = [dict(r) for r in result]
    return results_dict


def suggest_related_publications(paper_title):
    query_paper_recommendation = """
    MATCH (n:ns0__Publication)-[r:ns0__belongToTopic]->(a:ns0__Topic) 
    WHERE n.ns0__hasTitle = $paper_title

    // Randomize the order and select 3 topics
    WITH a.uri AS topicUri, n.ns0__hasTitle AS title, rand() AS randomOrder
    ORDER BY randomOrder
    LIMIT 3

    // Fetch other papers associated with these randomly selected topics
    MATCH (otherPapers:ns0__Publication)-[:ns0__belongToTopic]->(relatedTopics:ns0__Topic)
    WHERE relatedTopics.uri = topicUri
    RETURN title, topicUri, otherPapers.ns0__hasTitle AS relatedPaperTitle, otherPapers.ns0__hasPdfPath as path
    """
    parameters = {"paper_title": paper_title}
    result = run_query(query_paper_recommendation, parameters)
    results_dict = [dict(r) for r in result]
    return results_dict
