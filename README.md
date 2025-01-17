# Search Engine Project

## Overview

This is a web-based search engine built with Python and Flask. It includes a web crawler for fetching and indexing content, a Whoosh-based search engine for querying data, and a simple interface for displaying results. It supports fuzzy matching and missing word detection and uses TF-IDF as a ranking system.

## Features

- **Web Crawling**: Fetches and indexes content from a domain.
- **Search Functionality**: Supports keyword searches with fuzzy matching.
- **Missing Words**: Shows query words that did not match exactly.
- **Ranking**: Results are ranked using TF-IDF scoring for relevance + the number of matching words in the search.

## Running the Project

### Prerequisites

- Python 3.8+
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```

### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/imarouani/search.git
   cd search-engine
   ```
2. Run the application:
   ```bash
   python search.py
   ```
3. Access the app at: `http://127.0.0.1:5000`

### Run the Crawler

To rebuild the index, run:

```bash
python -c "from crwl import crawl; crawl()"
```

## Crawling Algorithm

The crawler starts at a base URL, fetches HTML pages, and follows internal links. It uses BeautifulSoup for parsing and Whoosh for indexing. Indexed data includes page titles, content, and teasers.

### Customization

- Update `base_url` in `crwl.py` to change the domain.
- Modify `is_valid_link` to include/exclude file types.

## Fuzzy Matching

Fuzzy matching handles typos or variations. For example, searching "platipus" will return results for "platypus" but show "platipus" as a missing word.

## Missing Words

Words not exactly matching the indexed content are listed as "Missing Words" to help refine the query.
