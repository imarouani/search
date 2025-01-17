from flask import Flask, request, render_template, url_for
from whoosh.index import open_dir
from whoosh.qparser import QueryParser, FuzzyTermPlugin
import os

# Get the absolute path of the current file
main_folder = os.path.dirname(os.path.abspath(__file__))

# Set dynamic paths for templates and Whoosh index
templates_path = os.path.join(main_folder, 'templates')
whoosh_index_path = os.path.join(main_folder, 'whoosh_index')

# Create the Flask app with the dynamic template folder
app = Flask(__name__, template_folder=templates_path)

# Search function (remains the same, just use the dynamic whoosh_index_path)
def search(query):
    """Search the Whoosh index for pages containing any query words."""
    if not os.path.exists(whoosh_index_path) or not os.listdir(whoosh_index_path):
        return [], "Error: Index does not exist. Please run the crawler script first."

    ix = open_dir(whoosh_index_path)
    results = []
    query = query.lower().strip()
    words = query.split()

    from whoosh.lang.porter import stem  # For manual stemming
    stemmed_words = [stem(word) for word in words]

    with ix.searcher() as searcher:
        qp = QueryParser("text", schema=ix.schema)
        qp.add_plugin(FuzzyTermPlugin())
        exact_query = " OR ".join(stemmed_words)
        fuzzy_query = " OR ".join(f"{word}~" for word in stemmed_words)
        combined_query = f"({exact_query}) OR ({fuzzy_query})"
        q = qp.parse(combined_query)

        hits = searcher.search(q, limit=None, terms=True)
        for hit in hits:
            results.append({
                "url": hit["url"],
                "title": hit["title"],
                "teaser": hit["teaser"],
                "matching_words": [word for word in words if word in hit.highlights("text")],
                "tfidf_score": hit.score,
            })

    results.sort(key=lambda x: x["tfidf_score"], reverse=True)
    return results, None


@app.route("/")
def home():
    """Home page with a search form."""
    return render_template("index.html")


@app.route("/search")
def search_page():
    """Process the search query and return results."""
    query = request.args.get("q", "").strip()
    if not query:
        return render_template("index.html", error="Please enter a search query.")

    results, error = search(query)
    if error:
        return render_template("index.html", error=error)

    return render_template("results.html", query=query, results=results)

if __name__ == "__main__":
    app.run()
