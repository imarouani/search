import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from whoosh.index import create_in
from whoosh.fields import Schema, TEXT, ID
from whoosh.analysis import StemmingAnalyzer
import os
import shutil
import re

# Base URL of the website to crawl
base_url = "https://vm009.rz.uos.de/crawl/index.html"
prefix = "https://vm009.rz.uos.de/"  # Only follow links within this domain

# Initialize structures
agenda = [base_url]  # Queue of URLs to visit
visited_urls = set()  # Keep track of visited URLs to avoid duplicates

# Whoosh index directory
index_dir = "whoosh_index"

# Define schema for the index
schema = Schema(
    url=ID(stored=True, unique=True),  # Store URLs
    title=TEXT(stored=True, analyzer=StemmingAnalyzer()),           # Store titles with stemming
    text=TEXT(stored=True, analyzer=StemmingAnalyzer()),            # Store text content with stemming
    teaser=TEXT(stored=True, analyzer=StemmingAnalyzer())           # Store teaser text with stemming
)

def normalize_text(text):
    """Normalize text by removing excessive whitespace and special characters."""
    text = re.sub(r"\s+", " ", text)  # Collapse multiple spaces
    text = re.sub(r"[\n\t]+", " ", text)  # Remove newlines and tabs
    text = text.strip()  # Trim leading and trailing whitespace
    return text

def fetch_page(url):
    """Fetch a page and return the BeautifulSoup object."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.content, "html.parser")
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def index_page(url, soup, writer):
    """Extract the full text content of a page and store it in the Whoosh index."""
    if soup is None:
        return

    # Extract text content
    text = soup.get_text(separator=" ", strip=True)  # Get all text content as a single string
    text = normalize_text(text)  # Normalize text

    title = soup.title.string.strip() if soup.title else "No Title"
    title = normalize_text(title)  # Normalize title

    # Remove the title from the beginning of the text if it appears
    if text.startswith(title):
        text = text[len(title):].strip()

    # Generate teaser text
    teaser = text[:150] + "..." if len(text) > 150 else text

    # Add to Whoosh index
    writer.update_document(url=url, title=title, text=text, teaser=teaser)

def is_valid_link(link):
    """Check if a link is valid and within the same domain."""
    return (
        link.startswith(prefix) and  # Internal links only
        not link.endswith(('.jpg', '.png', '.pdf', '.css', '.js'))  # Skip non-HTML files
    )

def crawl():
    """Crawl the website starting from the base URL and create the index."""
    if os.path.exists(index_dir):
        shutil.rmtree(index_dir)  # Clear the index directory to rebuild
    os.mkdir(index_dir)

    # Create a new index
    ix = create_in(index_dir, schema)
    writer = ix.writer()

    while agenda:
        url = agenda.pop()
        if url in visited_urls:
            continue

        print(f"Fetching: {url}")
        visited_urls.add(url)

        # Fetch and parse the page
        soup = fetch_page(url)
        if soup is None:
            continue

        # Index the page content
        index_page(url, soup, writer)

        # Find and queue new links
        for link_tag in soup.find_all('a', href=True):
            absolute_link = urljoin(url, link_tag['href'])
            if is_valid_link(absolute_link) and absolute_link not in visited_urls:
                agenda.append(absolute_link)

    writer.commit()  # Save the index
    print("Crawling and indexing completed!")

if __name__ == "__main__":
    crawl()
