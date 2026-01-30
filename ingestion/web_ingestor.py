import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "College-RAG-Ingestion-Bot"
}

def ingest_web(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    return soup.get_text(separator=" ")
