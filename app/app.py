import json

from flask import Flask, render_template, request
from werkzeug.exceptions import UnsupportedMediaType

from neo4j_connection import search_publication_by_author_alias, search_publications_by_topic, \
    search_publications_by_field_of_study, suggest_related_publications, search_paper_references, search_paper_details

app = Flask(__name__)


def get_search_value_from_request():
    search_value = None
    is_json = True
    try:
        search_value = request.json.get('search-value')
    except UnsupportedMediaType as e:
        pass
    if not search_value:
        search_value = request.form.get('search-value')
        is_json = False
    return search_value, is_json


def render_query_results(results, is_json):
    if results:
        fields = list(results[0].keys())
    else:
        fields = []
    if is_json:
        return json.dumps(results)
    return render_template(
        "simple_publication_results.html",
        title="Resultados",
        results=results,
        fields=fields
    )


@app.route("/")
def view_home():
    return render_template("index.html", title="Home")


@app.route("/author", methods=['GET'])
def view_autor_search():
    return render_template(
        "search_page.html",
        title="Autor",
        searched_object="autores",
        search_criteria="nombre"
    )


@app.route("/author", methods=['POST'])
def view_publication_by_author_alias():
    name, is_json = get_search_value_from_request()
    results = search_publication_by_author_alias(name=name)
    return render_query_results(results, is_json)


@app.route("/topic", methods=['GET'])
def view_topic():
    return render_template(
        "search_page.html",
        title="Topico",
        searched_object="publicaciones",
        search_criteria="topico"
    )


@app.route("/topic", methods=['POST'])
def view_publications_by_topic():
    topic_uri, is_json = get_search_value_from_request()
    results = search_publications_by_topic(topic_uri=topic_uri)
    return render_query_results(results, is_json)


@app.route("/field-of-study", methods=['GET'])
def view_campo_de_estudio():
    return render_template(
        "search_page.html",
        title="Campo de estudio",
        searched_object="publicaciones",
        search_criteria="campo de estudio"
    )


@app.route("/field-of-study", methods=['POST'])
def view_publications_by_field_of_study():
    field_of_study_uri, is_json = get_search_value_from_request()
    results = search_publications_by_field_of_study(field_of_study_uri=field_of_study_uri)
    return render_query_results(results, is_json)


@app.route("/publication-suggestion", methods=['GET'])
def view_publication_suggestion():
    return render_template(
        "search_page.html",
        title="Topico",
        searched_object="publicaciones relacionadas",
        search_criteria="uri de publicacion"
    )


@app.route("/publication-suggestion", methods=['POST'])
def view_related_publications():
    paper_uri, is_json = get_search_value_from_request()
    results = suggest_related_publications(paper_uri=paper_uri)
    return render_query_results(results, is_json)


@app.route("/publication-details", methods=['GET'])
def view_publication_details():
    return render_template(
        "search_page.html",
        title="Referencias",
        searched_object="detalles",
        search_criteria="uri de publicacion"
    )


@app.route("/publication-details", methods=['POST'])
def view_publication_details():
    oublication_uri, is_json = get_search_value_from_request()
    results = search_paper_details(publication_uri=oublication_uri)
    return render_query_results(results, is_json)


@app.route("/topics-barplot")
def view_barplot_topics():
    return render_template("topic_bar.html")


@app.route("/topics-graph")
def view_connection_topics_graph():
    return render_template("topic_nx.html")


if __name__ == '__main__':
    app.run(debug=True)
