from apify_client import ApifyClient
import pandas as pd

# Use your persistent token
client = ApifyClient("")

def scrape_diverse_benchmark(brand_name, actor_id, url):
    print(f"\n Scraping {brand_name} 2026 Strategy Data (50 Items)")
    
    # Using 'startUrl' as the standard for these actors
    run_input = {
        "startUrl": url,
        "results_wanted": 50, 
    }

    print(f"Agent {actor_id} is analyzing the Spring 2026 collection...")
    run = client.actor(actor_id).call(run_input=run_input)
    
    items = client.dataset(run["defaultDatasetId"]).list_items().items
    df = pd.DataFrame(items)
    
    # Save with a unique name to prevent overwriting during your demo
    file_path = f"data/raw/{brand_name.lower()}_benchmarks_2026.csv"
    df.to_csv(file_path, index=False)
    print(f"Success! {len(df)} diverse items saved to: {file_path}")

#  STRATEGIC EXECUTION

# 1. ZARA: Premium Trends (Dresses, Outerwear, Tailoring)
scrape_diverse_benchmark(
    "Zara", 
    "shahidirfan/zara-product-scraper", 
    "https://www.zara.com/us/en/woman-new-in-l1180.html"
)

# 2. H&M: Mass-Market Basics (Spring Essentials, Knitwear, Denim)
scrape_diverse_benchmark(
    "HM", 
    "shahidirfan/h-m-product-scraper", 
    "https://www2.hm.com/en_us/women/new-arrivals/view-all.html"
)
