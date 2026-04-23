import requests
from bs4 import BeautifulSoup

# Trying a post that is confirmed to have many comments
url = "https://jolynneshane.com/my-style-goals-for-2026.html"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

print(f"Connecting to: {url}...")
response = requests.get(url, headers=headers)

if response.status_code != 200:
    print(f"Failed to connect. Status Code: {response.status_code}")
else:
    soup = BeautifulSoup(response.text, 'html.parser')

    # 1. Scrape Content (The 'Expert' View)
    # Looking for the main article wrapper
    article = soup.find('article') or soup.find('div', class_='entry-content')
    if article:
        print("Successfully found the blog post!")
        # Save first 500 chars to verify
        with open("blog_content_preview.txt", "w", encoding="utf-8") as f:
            f.write(article.get_text()[:1000])
    else:
        print("Could not find article body.")

    # 2. Scrape Comments (The 'Consumer' Sentiment)
    # We are going to look for common WordPress comment patterns
    comments = []
    
    # Try multiple common tags found on her site
    potential_comments = soup.find_all('div', class_='comment-content') + \
                         soup.find_all('div', class_='comment-body') + \
                         soup.find_all('article', class_='comment-body')

    for item in potential_comments:
        # Extract text and ignore the 'Reply' buttons and dates
        text = item.get_text().strip()
        if text and len(text) > 10: # Ignore tiny fragments
            comments.append(text)

    if len(comments) > 0:
        print(f"Success! Collected {len(comments)} consumer comments.")
        with open("scripts/jolynne_sentiment_data.txt", "w", encoding="utf-8") as f:
            for c in comments:
                # Cleaning the text slightly
                clean_comment = " ".join(c.split())
                f.write(clean_comment + "\n---\n")
        print("Data saved to: scripts/jolynne_sentiment_data.txt")
    else:
        print("No comments found. The site may require a 'session' or JS.")