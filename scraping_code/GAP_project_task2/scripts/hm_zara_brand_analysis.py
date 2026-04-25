import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def generate_task3_master_report():
    # Load Data (Read files)
    hm_df = pd.read_csv('data/raw/hm_benchmarks_2026.csv')
    zara_df = pd.read_csv('data/raw/zara_benchmarks_2026.csv')

    # Standardize Names for the entire script
    hm_df = hm_df.rename(columns={'productName': 'name', 'colorName': 'color_col'})
    zara_df = zara_df.rename(columns={'display_name': 'name', 'available_color_names': 'color_col'})
    
    hm_df['Brand'] = 'H&M (Mass Market)'
    zara_df['Brand'] = 'Zara (Premium Trend)'

    # GRAPH 1: Price Architecture (Positioning) 
    plt.figure(figsize=(10, 6))
    combined = pd.concat([hm_df[['price', 'Brand']], zara_df[['price', 'Brand']]])
    sns.boxplot(x='Brand', y='price', data=combined, hue='Brand', palette=['#003d7c', '#da291c'], legend=False)
    plt.title("2026 Price Architecture: Premium Trend vs. Mass Market", fontsize=14, fontweight='bold')
    plt.ylabel("Price (USD)")
    plt.savefig('outputs/charts/price_architecture.png')
    plt.close() # Clean up memory

    # GRAPH 2: Color Strategy 
    fig2, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 9))
    
    # H&M Colors
    hm_df['color_col'].value_counts().head(8).plot(kind='pie', ax=ax1, autopct='%1.1f%%', 
                                                 startangle=140, cmap='Pastel1', title="H&M Color Strategy")
    ax1.set_ylabel("")

    # Zara Colors (with 'explosion' logic for multiple colors)
    zara_colors_raw = zara_df['color_col'].dropna().astype(str)
    # This line removes the brackets [ ] and the single quotes '
    zara_colors_clean = zara_colors_raw.str.replace(r"[\[\]']", "", regex=True)
    zara_final_counts = zara_colors_clean.str.split(',').explode().str.strip().value_counts().head(8)
    zara_final_counts.plot(kind='pie', ax=ax2, autopct='%1.1f%%', startangle=140, 
                      cmap='YlOrRd_r', title="Zara Color Strategy (Premium Trend)")
    ax2.set_ylabel("")
    
    plt.tight_layout()
    plt.savefig('outputs/charts/color_strategy_comparison.png')
    plt.close()

    # GRAPH 3: Style DNA (Keyword Frequency)
    def get_keywords(df):
        # Filters out brands and filler words to show actual styles
        words = df['name'].str.lower().str.split(expand=True).stack().value_counts()
        ignore = ['and', 'with', 'the', 'in', 'of', 'for', 'a', '-', '&', 'us', 'zara', 'h&m', 'piece', 'kids']
        return words[~words.index.isin(ignore)].head(10)

    fig3, (ax3, ax4) = plt.subplots(1, 2, figsize=(16, 7))
    get_keywords(hm_df).plot(kind='bar', ax=ax3, color='#003d7c', title="H&M Style DNA")
    get_keywords(zara_df).plot(kind='bar', ax=ax4, color='#da291c', title="Zara Style DNA")

    plt.tight_layout()
    plt.savefig('outputs/charts/style_dna_final.png')
    plt.close()
    
    print("\n STRATEGIC ANALYSIS COMPLETE")
    print("1. Price Architecture -> outputs/charts/price_architecture.png")
    print("2. Color Strategy    -> outputs/charts/color_strategy_comparison.png")
    print("3. Style DNA         -> outputs/charts/style_dna_final.png")

generate_task3_master_report()
