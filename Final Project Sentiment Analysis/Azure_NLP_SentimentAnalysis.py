import os
import re
import json
import time
import pandas as pd
import matplotlib.pyplot as plt

from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans


AZURE_LANGUAGE_KEY = ""
AZURE_LANGUAGE_ENDPOINT = ""


reddit_file = "reddit_outputs.parquet"
youtube_file = "youtube_sentiment_input.jsonl"
blog_keywords_file = "blog_keywords.csv"
hm_keywords_file = "hm_top_keywords.csv"


client = TextAnalyticsClient(
    endpoint=AZURE_LANGUAGE_ENDPOINT,
    credential=AzureKeyCredential(AZURE_LANGUAGE_KEY)
)


def clean_text(text):
    text = str(text)
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def assign_brand(row):
    full_text = " ".join([
        str(row.get("text", "")),
        str(row.get("video_title", "")),
        str(row.get("source_query", "")),
        str(row.get("title", "")),
        str(row.get("body", "")),
        str(row.get("selftext", ""))
    ]).lower()

    if "old navy" in full_text or "oldnavy" in full_text:
        return "Old Navy"
    elif "banana republic" in full_text or "bananarepublic" in full_text:
        return "Banana Republic"
    elif "gap inc" in full_text or " gap " in f" {full_text} ":
        return "Gap"
    else:
        return "General Fashion"


def load_reddit(file_path):
    df = pd.read_parquet(file_path)
    df["source"] = "Reddit"

    possible_text_cols = ["text", "body", "comment", "selftext", "title"]

    text_cols = [col for col in possible_text_cols if col in df.columns]

    if len(text_cols) == 0:
        raise ValueError("No usable text column found in Reddit file.")

    df["text"] = df[text_cols].fillna("").astype(str).agg(" ".join, axis=1)
    return df


def load_youtube(file_path):
    records = []

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))

    df = pd.DataFrame(records)
    df["source"] = "YouTube"
    return df


reddit_df = load_reddit(reddit_file)
youtube_df = load_youtube(youtube_file)


combined_df = pd.concat([reddit_df, youtube_df], ignore_index=True, sort=False)

combined_df["text"] = combined_df["text"].apply(clean_text)
combined_df = combined_df[combined_df["text"] != ""]
combined_df = combined_df[combined_df["text"].str.lower() != "nan"]

combined_df["brand"] = combined_df.apply(assign_brand, axis=1)

brand_df = combined_df[
    combined_df["brand"].isin(["Old Navy", "Gap", "Banana Republic"])
].copy()

if len(brand_df) == 0:
    print("No direct Gap Inc. brand mentions found. Falling back to General Fashion trend analysis.")
    brand_df = combined_df.copy()


brand_df = brand_df.reset_index(drop=True)
brand_df["document_id"] = brand_df.index.astype(str)


def azure_analyze_batch(texts):
    docs = []

    for i, text in enumerate(texts):
        docs.append({
            "id": str(i),
            "language": "en",
            "text": str(text)[:5000]
        })

    sentiment_results = client.analyze_sentiment(
        documents=docs,
        show_opinion_mining=True
    )

    key_phrase_results = client.extract_key_phrases(
        documents=docs
    )

    output = []

    for sent, phrases in zip(sentiment_results, key_phrase_results):
        if sent.is_error:
            sentiment = "error"
            confidence_positive = None
            confidence_neutral = None
            confidence_negative = None
        else:
            sentiment = sent.sentiment
            confidence_positive = sent.confidence_scores.positive
            confidence_neutral = sent.confidence_scores.neutral
            confidence_negative = sent.confidence_scores.negative

        if phrases.is_error:
            key_phrases = []
        else:
            key_phrases = phrases.key_phrases

        output.append({
            "azure_sentiment": sentiment,
            "confidence_positive": confidence_positive,
            "confidence_neutral": confidence_neutral,
            "confidence_negative": confidence_negative,
            "key_phrases": ", ".join(key_phrases)
        })

    return output


batch_size = 10
azure_outputs = []

for start in range(0, len(brand_df), batch_size):
    end = start + batch_size
    batch_texts = brand_df["text"].iloc[start:end].tolist()

    try:
        batch_output = azure_analyze_batch(batch_texts)
        azure_outputs.extend(batch_output)
        print(f"Processed rows {start} to {end}")
        time.sleep(1)

    except Exception as e:
        print(f"Error on rows {start} to {end}: {e}")

        for _ in batch_texts:
            azure_outputs.append({
                "azure_sentiment": "error",
                "confidence_positive": None,
                "confidence_neutral": None,
                "confidence_negative": None,
                "key_phrases": ""
            })


azure_df = pd.DataFrame(azure_outputs)
brand_df = pd.concat([brand_df.reset_index(drop=True), azure_df.reset_index(drop=True)], axis=1)


sentiment_summary = brand_df.groupby(
    ["brand", "azure_sentiment"]
).size().reset_index(name="count")

sentiment_pivot = sentiment_summary.pivot(
    index="brand",
    columns="azure_sentiment",
    values="count"
).fillna(0)

for col in ["positive", "neutral", "negative", "mixed"]:
    if col not in sentiment_pivot.columns:
        sentiment_pivot[col] = 0

sentiment_pivot["Total"] = sentiment_pivot.sum(axis=1)
sentiment_pivot["Positive %"] = sentiment_pivot["positive"] / sentiment_pivot["Total"]
sentiment_pivot["Neutral %"] = sentiment_pivot["neutral"] / sentiment_pivot["Total"]
sentiment_pivot["Negative %"] = sentiment_pivot["negative"] / sentiment_pivot["Total"]
sentiment_pivot["Mixed %"] = sentiment_pivot["mixed"] / sentiment_pivot["Total"]

sentiment_pivot = sentiment_pivot.reset_index()


phrase_rows = []

for _, row in brand_df.iterrows():
    phrases = str(row["key_phrases"]).split(",")

    for phrase in phrases:
        phrase = phrase.strip().lower()

        if phrase != "":
            phrase_rows.append({
                "brand": row["brand"],
                "source": row["source"],
                "key_phrase": phrase
            })

key_phrase_df = pd.DataFrame(phrase_rows)

if len(key_phrase_df) > 0:
    key_phrase_summary = key_phrase_df.groupby(
        ["brand", "key_phrase"]
    ).size().reset_index(name="count")

    key_phrase_summary = key_phrase_summary.sort_values(
        ["brand", "count"],
        ascending=[True, False]
    )
else:
    key_phrase_summary = pd.DataFrame(columns=["brand", "key_phrase", "count"])


cluster_input = brand_df["text"].fillna("").astype(str)

vectorizer = TfidfVectorizer(
    stop_words="english",
    max_features=1000,
    min_df=2
)

X = vectorizer.fit_transform(cluster_input)

cluster_count = min(5, len(brand_df))

if cluster_count >= 2:
    kmeans = KMeans(
        n_clusters=cluster_count,
        random_state=42,
        n_init=10
    )

    brand_df["theme_cluster"] = kmeans.fit_predict(X)

    terms = vectorizer.get_feature_names_out()
    cluster_keywords = []

    for cluster_num in range(cluster_count):
        top_terms = kmeans.cluster_centers_[cluster_num].argsort()[-12:][::-1]
        keywords = [terms[i] for i in top_terms]

        cluster_keywords.append({
            "theme_cluster": cluster_num,
            "top_keywords": ", ".join(keywords)
        })

    cluster_keywords_df = pd.DataFrame(cluster_keywords)

else:
    brand_df["theme_cluster"] = 0
    cluster_keywords_df = pd.DataFrame({
        "theme_cluster": [0],
        "top_keywords": ["Not enough records for clustering"]
    })


theme_summary = brand_df.groupby(
    ["brand", "theme_cluster"]
).size().reset_index(name="count")


def build_strategy_assessment(row):
    brand = row["brand"]

    positive = row.get("Positive %", 0)
    negative = row.get("Negative %", 0)

    if brand == "Old Navy":
        category = "Value Clothing"
        assessment = "Consumer discussion can be used to monitor affordability, fit, family basics, and perceived quality."
        impact = "Supports value-focused product decisions while identifying quality or sizing issues that may weaken loyalty."

    elif brand == "Gap":
        category = "Mid-Tier Casual / Modern Essentials"
        assessment = "NLP helps identify whether consumers associate Gap with denim, basics, style relevance, or brand confusion."
        impact = "Supports clearer differentiation between Old Navy value and Banana Republic premium positioning."

    elif brand == "Banana Republic":
        category = "Premium Lifestyle / Elevated Workwear"
        assessment = "NLP helps evaluate premium sentiment, workwear associations, quality perceptions, and fashion credibility."
        impact = "Supports higher-margin product strategy and premium brand positioning."

    else:
        category = "General Fashion"
        assessment = "NLP identifies broad fashion themes and sentiment patterns."
        impact = "Supports trend monitoring and external market benchmarking."

    if negative > 0.35:
        impact += " High negative sentiment indicates a risk area requiring deeper review."
    elif positive > 0.50:
        impact += " Strong positive sentiment indicates potential brand strength to reinforce."

    return pd.Series([category, assessment, impact])


strategy_df = sentiment_pivot.copy()
strategy_df[["Category", "Data-Driven Strategy Assessment", "Impact"]] = strategy_df.apply(
    build_strategy_assessment,
    axis=1
)

strategy_df = strategy_df[
    [
        "brand",
        "Category",
        "Data-Driven Strategy Assessment",
        "Impact",
        "Positive %",
        "Neutral %",
        "Negative %",
        "Mixed %",
        "Total"
    ]
]

strategy_df = strategy_df.rename(columns={"brand": "Brand"})


blog_keywords_df = pd.read_csv(blog_keywords_file)
hm_keywords_df = pd.read_csv(hm_keywords_file)

blog_keywords_df["source"] = "Fashion Blog Keywords"
hm_keywords_df["source"] = "H&M Benchmark Keywords"

keyword_benchmark_df = pd.concat(
    [blog_keywords_df, hm_keywords_df],
    ignore_index=True
)


brand_df.to_csv("gap_inc_azure_nlp_full_output.csv", index=False)
sentiment_pivot.to_csv("gap_inc_azure_sentiment_summary.csv", index=False)
key_phrase_summary.to_csv("gap_inc_azure_key_phrase_summary.csv", index=False)
cluster_keywords_df.to_csv("gap_inc_theme_cluster_keywords.csv", index=False)
theme_summary.to_csv("gap_inc_theme_cluster_summary.csv", index=False)
strategy_df.to_csv("gap_inc_brand_strategy_table.csv", index=False)
keyword_benchmark_df.to_csv("external_keyword_benchmark_summary.csv", index=False)


with pd.ExcelWriter("gap_inc_nlp_analysis_package.xlsx", engine="openpyxl") as writer:
    brand_df.to_excel(writer, sheet_name="Full NLP Output", index=False)
    sentiment_pivot.to_excel(writer, sheet_name="Sentiment Summary", index=False)
    key_phrase_summary.to_excel(writer, sheet_name="Key Phrases", index=False)
    cluster_keywords_df.to_excel(writer, sheet_name="Cluster Keywords", index=False)
    theme_summary.to_excel(writer, sheet_name="Theme Summary", index=False)
    strategy_df.to_excel(writer, sheet_name="Strategy Table", index=False)
    keyword_benchmark_df.to_excel(writer, sheet_name="External Keywords", index=False)


plt.figure(figsize=(10, 6))
sentiment_pivot.set_index("brand")[["Positive %", "Neutral %", "Negative %", "Mixed %"]].plot(
    kind="bar",
    figsize=(10, 6)
)
plt.title("Azure NLP Sentiment Distribution by Gap Inc. Brand")
plt.ylabel("Percentage of Text Records")
plt.xlabel("Brand")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig("gap_inc_azure_sentiment_distribution.png")
plt.show()


plt.figure(figsize=(10, 6))
theme_summary.pivot(
    index="brand",
    columns="theme_cluster",
    values="count"
).fillna(0).plot(
    kind="bar",
    figsize=(10, 6)
)
plt.title("NLP Theme Cluster Distribution by Gap Inc. Brand")
plt.ylabel("Number of Text Records")
plt.xlabel("Brand")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig("gap_inc_theme_cluster_distribution.png")
plt.show()


print("\nSentiment Summary")
print(sentiment_pivot)

print("\nTop Key Phrases")
print(key_phrase_summary.head(30))

print("\nTheme Cluster Keywords")
print(cluster_keywords_df)

print("\nStrategy Table")
print(strategy_df)

print("\nFiles created:")
print("gap_inc_azure_nlp_full_output.csv")
print("gap_inc_azure_sentiment_summary.csv")
print("gap_inc_azure_key_phrase_summary.csv")
print("gap_inc_theme_cluster_keywords.csv")
print("gap_inc_theme_cluster_summary.csv")
print("gap_inc_brand_strategy_table.csv")
print("external_keyword_benchmark_summary.csv")
print("gap_inc_nlp_analysis_package.xlsx")
print("gap_inc_azure_sentiment_distribution.png")
print("gap_inc_theme_cluster_distribution.png")