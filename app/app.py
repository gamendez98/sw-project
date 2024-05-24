from flask import Flask, render_template, request

from app.neo4j_connection import search_publication_by_author_alias, search_publications_by_topic, \
    search_publications_by_field_of_study, suggest_related_publications

app = Flask(__name__)


def render_query_results(results):
    if results:
        fields = list(results[0].keys())
    else:
        fields = []
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
    name = request.form.get('search-value')
    results = search_publication_by_author_alias(name=name)
    return render_query_results(results)


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
    topic_uri = request.form.get('search-value')
    results = search_publications_by_topic(topic_uri=topic_uri)
    return render_query_results(results)


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
    field_of_study_uri = request.form.get('search-value')
    results = search_publications_by_field_of_study(field_of_study_uri=field_of_study_uri)
    return render_query_results(results)


@app.route("/publication-suggestion", methods=['GET'])
def view_publication_suggestion():
    return render_template(
        "search_page.html",
        title="Topico",
        searched_object="publicaciones relacionadas",
        search_criteria="publicacion"
    )


@app.route("/publication-suggestion", methods=['POST'])
def view_related_publications():
    paper_title = request.form.get('search-value')
    results = suggest_related_publications(paper_title=paper_title)
    return render_query_results(results)


if __name__ == '__main__':
    app.run(debug=True)
