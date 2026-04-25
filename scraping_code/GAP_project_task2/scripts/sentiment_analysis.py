import pandas as pd
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import re

# Initialize AI Agent for Sentiment
nltk.download('vader_lexicon')
sia = SentimentIntensityAnalyzer()

def analyze_sentiment_cleaned(text):
    # Convert to string and lowercase
    text = str(text).lower()
    
    # 1. CLEANING: Remove encoding artifacts and noise fragments
    # This helps fix the 'neutral' scores caused by messy text
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    # 2. FILTERING: Ignore rows that are too short (like "Tip #1" or "0") 
    # These often result in a 0.0 score because they lack emotional keywords
    if len(text) < 20 or text.isdigit():
        return None 
    
    # 3. ANALYSIS: Return the compound score
    return sia.polarity_scores(text)['compound']

# Load both datasets
try:
    # 1. Editorial Data (Who What Wear)
    df_www = pd.read_csv('data/raw/fashion_blog_raw.csv')
    df_www['source'] = 'Who What Wear (Editorial)'
    df_www = df_www.rename(columns={'paragraphs': 'text_content'})
    
    # 2. Consumer Data (Jo-Lynne Shane)
    with open('scripts/jolynne_sentiment_data.txt', 'r', encoding='utf-8') as f:
        raw_text = f.read()
    
    comment_list = [c.strip() for c in raw_text.split('---') if len(c.strip()) > 5]
    df_js = pd.DataFrame(comment_list, columns=['text_content'])
    df_js['source'] = 'Jo-Lynne Shane (Consumer)'

    # Combine for Task 3 Comparative Analysis
    combined_df = pd.concat([df_www[['text_content', 'source']], df_js[['text_content', 'source']]], ignore_index=True)

    # UPDATED ANALYSIS STEP 
    # Apply the cleaned analysis function
    combined_df['sentiment_score'] = combined_df['text_content'].apply(analyze_sentiment_cleaned)
    
    # Remove the 'None' rows (the noise) so your averages are more accurate for Task 3
    final_df = combined_df.dropna(subset=['sentiment_score']).copy()
    
    # Optional: Filter out scores that are exactly 0 to show only strong opinions
    # final_df = final_df[final_df['sentiment_score'] != 0]

    # Generate Insights for Presentation
    summary = final_df.groupby('source')['sentiment_score'].mean()
    print("\n Average Sentiment by Source (Cleaned)")
    print(summary)

    # Save for Final Project Deliverables
    final_df.to_csv('data/processed/combined_sentiment_results.csv', index=False)
    print("\nSuccess: Results saved to data/processed/combined_sentiment_results.csv")

except Exception as e:
    print(f"Error: {e}")
    
