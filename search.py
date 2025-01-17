from flask import Flask, request, render_template
from whoosh.index import open_dir
from whoosh.qparser import QueryParser, FuzzyTermPlugin
import os

app = Flask(__name__)

# Whoosh index directory
index_dir = "whoosh_index"

from whoosh.analysis import StemmingAnalyzer
from whoosh.lang.porter import stem  # For manual stemming

def search(query):
    """Search the Whoosh index for pages containing any query words."""
    if not os.path.exists(index_dir) or not os.listdir(index_dir):
        return [], "Error: Index does not exist. Please run the crawler script first."

    ix = open_dir(index_dir)
    results = []
    query = query.lower().strip()
    words = query.split()  # Split the query into individual words

    # Apply stemming to query words to match the indexed terms
    from whoosh.lang.porter import stem  # For manual stemming
    stemmed_words = [stem(word) for word in words]

    with ix.searcher() as searcher:
        # Use Whoosh's built-in scoring system with QueryParser
        qp = QueryParser("text", schema=ix.schema)
        qp.add_plugin(FuzzyTermPlugin())  # Add fuzzy matching plugin

        # Create a query that includes both exact matches and fuzzy matches
        exact_query = " OR ".join(stemmed_words)  # Exact match query
        fuzzy_query = " OR ".join(f"{word}~" for word in stemmed_words)  # Fuzzy match query
        combined_query = f"({exact_query}) OR ({fuzzy_query})"
        q = qp.parse(combined_query)

        # Perform the search with term tracking enabled
        hits = searcher.search(q, limit=None, terms=True)  # Enable term tracking

        for hit in hits:
            url = hit["url"]
            title = hit["title"]
            teaser = hit["teaser"]
            content = hit["text"].lower()

            # Extract matched terms from Whoosh results and decode bytes to strings
            matched_terms = set(term.decode('utf-8').lower() for _, term in hit.matched_terms())
            print(f"Matched terms: {matched_terms}")  # Debugging log for matched terms

            # Determine matching and missing words based on stemmed terms
            matching_words = [word for word, stemmed_word in zip(words, stemmed_words) if stemmed_word in matched_terms]
            missing_words = [word for word, stemmed_word in zip(words, stemmed_words) if stemmed_word not in matched_terms]

            # Add Whoosh's TF-IDF score
            whoosh_score = hit.score

            # Calculate a simple rank based on the number of matching words
            rank = len(matching_words)

            results.append({
                "url": url,
                "title": title,
                "teaser": teaser,
                "matching_words": matching_words,
                "missing_words": missing_words,
                "tfidf_score": whoosh_score,  # Add Whoosh's TF-IDF score
                "rank": rank  # Add extra rank for matching words count
            })

    # Sort results by TF-IDF score in descending order, then by extra rank
    results.sort(key=lambda x: (x["tfidf_score"], x["rank"]), reverse=True)

    return results, None


@app.route("/")
def home():
    """Home page with a search form."""
    return render_template("index.html")

@app.route("/search")
def search_page():
    """Process the search query and return results."""
    query = request.args.get("q", "").strip()  # Get the query parameter from the URL
    if not query:
        return render_template("index.html", error="Please enter a search query.")

    results, error = search(query)
    if error:
        return render_template("index.html", error=error)

    return render_template("results.html", query=query, results=results)

if __name__ == "__main__":
    app.run()
