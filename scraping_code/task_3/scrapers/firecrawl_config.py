"""
Firecrawl Configuration
"""

FIRECRAWL_API_KEY = "fc-674263963d2e416d8395037d12018cf3"

# Scraping options for different sources
SCRAPE_OPTIONS = {
    "zara": {
        "formats": ["html", "markdown"],
        "onlyMainContent": True,
        "waitFor": 3000,
        "timeout": 20000
    },
    "vogue": {
        "formats": ["markdown"],
        "onlyMainContent": True,
        "timeout": 10000
    }
}
