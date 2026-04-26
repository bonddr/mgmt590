import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def generate_task3_master_report():
    # 1. Load Data
    hm_df = pd.read_csv('data/raw/hm_benchmarks_2026.csv')
    zara_df = pd.read_csv('data/raw/zara_benchmarks_2026.csv')

    # 2. Standardize Names
    hm_df = hm_df.rename(columns={'productName': 'name', 'colorName': 'color_col'})
    zara_df = zara_df.rename(columns={'display_name': 'name', 'available_color_names': 'color_col'})
    
    # GRAPH 1: Price Architecture
    plt.figure(figsize=(10, 6))
    combined = pd.concat([hm_df.assign(Brand='H&M (Mass Market)'), zara_df.assign(Brand='Zara (Premium Trend)')])
    sns.boxplot(x='Brand', y='price', data=combined, hue='Brand', palette=['#003d7c', '#da291c'], legend=False)
    plt.title("2026 Price Architecture: Premium Trend vs. Mass Market", fontsize=14, fontweight='bold')
    plt.ylabel("Price (USD)")
    plt.savefig('outputs/charts/price_architecture.png', dpi=300)
    plt.close()

    # GRAPH 2: Color Strategy 
    fig2, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10), constrained_layout=True)
    
    # H&M Logic
    hm_counts = hm_df['color_col'].dropna().astype(str).str.title().value_counts().head(8)
    # FIX: We create the color list from the palette first
    hm_colors = sns.color_palette("Pastel1", len(hm_counts))
    ax1.pie(hm_counts, autopct='%1.1f%%', startangle=140, labels=None, colors=hm_colors, wedgeprops={'edgecolor': 'white'})
    ax1.set_title("H&M: Mass-Market Neutral & Pastel Strategy", fontsize=18, fontweight='bold', pad=20)

    # Zara Logic
    zara_colors = zara_df['color_col'].dropna().astype(str).str.replace(r"[\[\]']", "", regex=True)
    zara_counts = zara_colors.str.split(',').explode().str.strip().str.title().value_counts().head(8)
    # FIX: We create the color list from the palette first
    zara_palette = sns.color_palette("YlOrRd_r", len(zara_counts))
    ax2.pie(zara_counts, autopct='%1.1f%%', startangle=140, labels=None, colors=zara_palette, wedgeprops={'edgecolor': 'white'})
    ax2.set_title("Zara: Premium Deep Neutral & Bold Strategy", fontsize=18, fontweight='bold', pad=20)

    fig2.text(0.5, 0.05, "Strategic Focus: H&M (High-Volume Basics) vs. Zara (High-Margin Trends)", 
              ha='center', fontsize=14, fontweight='bold', bbox=dict(facecolor='white', alpha=0.5))

    plt.savefig('outputs/charts/color_strategy_comparison.png', dpi=300)
    plt.close()

    # GRAPH 3: Style DNA 
    def get_keywords(df):
        words = df['name'].str.lower().str.split(expand=True).stack().value_counts()
        ignore = ['and', 'with', 'the', 'in', 'of', 'for', 'a', '-', '&', 'us', 'zara', 'h&m', 'piece', 'kids']
        return words[~words.index.isin(ignore)].head(10)

    fig3, (ax3, ax4) = plt.subplots(1, 2, figsize=(16, 7))
    get_keywords(hm_df).plot(kind='bar', ax=ax3, color='#003d7c', title="H&M Style DNA")
    get_keywords(zara_df).plot(kind='bar', ax=ax4, color='#da291c', title="Zara Style DNA")
    plt.tight_layout()
    plt.savefig('outputs/charts/style_dna_final.png', dpi=300)
    plt.close()

generate_task3_master_report()