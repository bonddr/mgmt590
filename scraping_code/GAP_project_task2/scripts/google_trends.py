from pytrends.request import TrendReq
import pandas as pd
import matplotlib.pyplot as plt
import os

# Create output folder if not exists
os.makedirs("outputs/charts", exist_ok=True)
os.makedirs("data/raw", exist_ok=True)

# Connect to Google Trends
pytrends = TrendReq(hl='en-US', tz=360)

# Keywords to analyze
keywords = [
    "oversized hoodie",
    "wide leg jeans",
    "neutral colors fashion",
    "linen pants women"
]

# Get data
pytrends.build_payload(keywords, timeframe='today 12-m')
data = pytrends.interest_over_time()

# Save CSV
data.to_csv("data/raw/google_trends.csv")

# Plot
data[keywords].plot(figsize=(10, 6))
plt.title("Fashion Trends Over Time")
plt.xlabel("Date")
plt.ylabel("Search Interest")
plt.legend()
plt.tight_layout()

# Save chart
plt.savefig("outputs/charts/google_trends.png")
plt.show()

print("Google Trends data collected and saved.")