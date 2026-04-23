import os
import requests
import pandas as pd
from bs4 import BeautifulSoup

os.makedirs("data/raw", exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def fetch_page(url):
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.text

def scrape_blog(url):
    html = fetch_page(url)
    soup = BeautifulSoup(html, "lxml")

    titles = []
    paragraphs = []

    # Get headings
    for h in soup.find_all(["h1", "h2", "h3"]):
        text = h.get_text(strip=True)
        if text:
            titles.append(text)

    # Get paragraphs
    for p in soup.find_all("p"):
        text = p.get_text(strip=True)
        if len(text) > 50:
            paragraphs.append(text)

    return titles, paragraphs

def main():
    url = "https://www.whowhatwear.com/fashion-trends"

    titles, paragraphs = scrape_blog(url)

    df = pd.DataFrame({
        "titles": pd.Series(titles),
        "paragraphs": pd.Series(paragraphs)
    })

    df.to_csv("data/raw/fashion_blog_raw.csv", index=False)

    print(df.head())
    print(f"Collected {len(df)} blog entries")

if __name__ == "__main__":
    main()