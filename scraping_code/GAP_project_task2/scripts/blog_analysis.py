import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt
import os

INPUT_FILE = "data/raw/fashion_blog_raw.csv"

os.makedirs("outputs/charts", exist_ok=True)

def extract_keywords(text_series, top_n=20):
    stopwords = {
    "the","and","for","with","this","that","are","was","from","you","your",
    "about","fashion","style","look","like","what","when","while","instead",
    "wrong","site","pair","you're","they","their","them","into","over",
    "under","more","less","very","just","also","than","then","there",
    "these","those","has","have","had","been","being","will","would",
    "could","should","can","may","might","do","does","did"
    }

    fashion_terms = [
        "oversized","linen","denim","tailored","neutral","minimal",
        "cropped","wide","leg","blazer","jacket","dress","pants",
        "tops","shirt","layering","structured","casual"
    ]

    words = []

    for text in text_series.dropna():
        for word in str(text).lower().split():
            word = word.strip(".,!?()[]{}-_/")
            if len(word) > 4 and word not in stopwords and word in fashion_terms:
                words.append(word)

    return Counter(words).most_common(top_n)

def main():
    df = pd.read_csv(INPUT_FILE)

    keywords = extract_keywords(df["paragraphs"])

    keyword_df = pd.DataFrame(keywords, columns=["keyword", "count"])

    keyword_df.to_csv("outputs/tables/blog_keywords.csv", index=False)

    plt.figure(figsize=(10, 5))
    plt.bar(keyword_df["keyword"], keyword_df["count"])
    plt.title("Top Fashion Blog Keywords")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig("outputs/charts/blog_keywords.png")
    plt.close()

    print(keyword_df.head())

if __name__ == "__main__":
    main()
