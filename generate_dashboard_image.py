import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch, Rectangle
import seaborn as sns

def generate_dashboard():
    os.makedirs('Dashboard', exist_ok=True)
    out_path = os.path.join('Dashboard', 'netflix_dashboard.png')

    cleaned_csv = os.path.join('Dataset', 'netflix_titles_cleaned.csv')
    df = pd.read_csv(cleaned_csv)
    print(f"Loaded {len(df)} rows for dashboard visualization.")

    # High-DPI figure setup
    plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
    plt.rcParams['font.family'] = 'sans-serif'
    
    # Palette
    bg_color = '#0F0F11'
    card_bg = '#18181C'
    border_color = '#282830'
    text_primary = '#FFFFFF'
    text_secondary = '#A0A0AA'
    netflix_red = '#E50914'
    movie_color = '#E50914'
    tv_color = '#3B82F6'
    accent_gray = '#4B5563'
    bar_fill_color = '#4F46E5'

    fig = plt.figure(figsize=(24, 13.5), facecolor=bg_color, dpi=150)
    gs = gridspec.GridSpec(
        nrows=4, 
        ncols=3, 
        figure=fig,
        height_ratios=[0.9, 1.2, 2.5, 2.5],
        hspace=0.28,
        wspace=0.18,
        left=0.04,
        right=0.96,
        top=0.94,
        bottom=0.04
    )

    # ----------------------------------------------------
    # ROW 0: Header & Interactive Filter Bar
    # ----------------------------------------------------
    ax_header = fig.add_subplot(gs[0, :])
    ax_header.set_facecolor(bg_color)
    ax_header.axis('off')

    # Dashboard Title
    ax_header.text(0.0, 0.75, "NETFLIX CONTENT ANALYTICS", color=text_primary, fontsize=24, fontweight='bold', va='center')
    ax_header.text(0.0, 0.40, "Exploring Netflix's Movies & TV Shows Across Time, Geography, Genres and Ratings", color=text_secondary, fontsize=12, va='center')

    # Draw interactive filters pill mockup on the right side
    filters = [
        ("Type", "All Content (Movie & TV)"),
        ("Release Year", "1925 - 2021"),
        ("Country", "Global (All Regions)"),
        ("Rating", "All Age Certifications")
    ]
    x_start = 0.48
    for lbl, val in filters:
        pill_rect = FancyBboxPatch((x_start, 0.28), 0.12, 0.48, boxstyle="round,pad=0.01,rounding_size=0.03",
                                   facecolor='#222228', edgecolor=border_color, linewidth=1.2)
        ax_header.add_patch(pill_rect)
        ax_header.text(x_start + 0.008, 0.60, lbl.upper(), color=netflix_red, fontsize=7.5, fontweight='bold')
        ax_header.text(x_start + 0.008, 0.40, val, color=text_primary, fontsize=8.5, fontweight='medium')
        x_start += 0.13

    # ----------------------------------------------------
    # ROW 1: KPI Cards (6 metrics across the grid)
    # ----------------------------------------------------
    kpi_ax = fig.add_subplot(gs[1, :])
    kpi_ax.set_facecolor(bg_color)
    kpi_ax.axis('off')

    kpi_metrics = [
        ("TOTAL TITLES", "8,807", "100% Catalog Volume", text_primary),
        ("MOVIES", "6,131", "69.6% Share of Library", movie_color),
        ("TV SHOWS", "2,676", "30.4% Share of Library", tv_color),
        ("COUNTRIES", "86", "Lead Production Nations", '#10B981'),
        ("UNIQUE GENRES", "42", "Distinct Categorizations", '#F59E0B'),
        ("AVG MOVIE RUNTIME", "99.6 min", "Typical Film Duration", '#EC4899')
    ]

    card_width = 0.152
    spacing = (1.0 - (card_width * 6)) / 5
    for i, (kpi_title, kpi_val, kpi_sub, val_col) in enumerate(kpi_metrics):
        cx = i * (card_width + spacing)
        card_patch = FancyBboxPatch((cx, 0.05), card_width, 0.90, boxstyle="round,pad=0.015,rounding_size=0.03",
                                    facecolor=card_bg, edgecolor=border_color, linewidth=1.2)
        kpi_ax.add_patch(card_patch)
        
        # Subtle top accent line
        line_patch = FancyBboxPatch((cx + 0.015, 0.90), card_width - 0.03, 0.04, boxstyle="square,pad=0",
                                    facecolor=val_col, edgecolor='none')
        kpi_ax.add_patch(line_patch)

        kpi_ax.text(cx + card_width/2, 0.68, kpi_title, color=text_secondary, fontsize=9.5, fontweight='bold', ha='center', va='center')
        kpi_ax.text(cx + card_width/2, 0.40, kpi_val, color=val_col, fontsize=21, fontweight='bold', ha='center', va='center')
        kpi_ax.text(cx + card_width/2, 0.18, kpi_sub, color=text_secondary, fontsize=8, ha='center', va='center')

    # Helper function to style chart panels
    def style_panel(ax, title):
        ax.set_facecolor(card_bg)
        ax.tick_params(colors=text_secondary, labelsize=9)
        for spine in ax.spines.values():
            spine.set_color(border_color)
            spine.set_linewidth(1.0)
        ax.set_title(title, color=text_primary, fontsize=12, fontweight='bold', pad=14, loc='left')

    # ----------------------------------------------------
    # ROW 2, COL 0: Movies vs TV Shows Donut Chart
    # ----------------------------------------------------
    ax_donut = fig.add_subplot(gs[2, 0])
    style_panel(ax_donut, "Movies vs TV Shows Catalog Breakdown")
    
    type_counts = df['type'].value_counts()
    wedges, texts, autotexts = ax_donut.pie(
        type_counts, 
        labels=type_counts.index,
        autopct='%1.1f%%',
        pctdistance=0.76,
        startangle=90,
        colors=[movie_color, tv_color],
        wedgeprops=dict(width=0.42, edgecolor=card_bg, linewidth=3),
        textprops=dict(color=text_primary, fontsize=10, fontweight='bold')
    )
    for at in autotexts:
        at.set_color('#FFFFFF')
        at.set_fontsize(11)
    ax_donut.text(0, 0, f"Total\n8,807", color=text_primary, fontsize=12, fontweight='bold', ha='center', va='center')

    # ----------------------------------------------------
    # ROW 2, COL 1: Content Ingestion Trend Over Time (2008-2021)
    # ----------------------------------------------------
    ax_trend = fig.add_subplot(gs[2, 1])
    style_panel(ax_trend, "Content Added Over Time (2012 - 2021)")
    
    yearly = (
        df[df['year_added'] >= 2012]
        .groupby(['year_added', 'type'])
        .size()
        .unstack(fill_value=0)
    )
    x_years = yearly.index
    ax_trend.plot(x_years, yearly['Movie'], marker='o', color=movie_color, linewidth=2.5, label='Movies Added')
    ax_trend.plot(x_years, yearly['TV Show'], marker='s', color=tv_color, linewidth=2.5, label='TV Shows Added')
    ax_trend.fill_between(x_years, yearly['Movie'], alpha=0.15, color=movie_color)
    ax_trend.fill_between(x_years, yearly['TV Show'], alpha=0.15, color=tv_color)
    
    ax_trend.set_xlabel("Year Added to Netflix", color=text_secondary, fontsize=9.5, labelpad=8)
    ax_trend.set_ylabel("Titles Added", color=text_secondary, fontsize=9.5, labelpad=8)
    ax_trend.grid(True, linestyle='--', alpha=0.15, color='#FFFFFF')
    ax_trend.legend(facecolor='#222228', edgecolor=border_color, labelcolor=text_primary, fontsize=8.5, loc='upper left')

    # ----------------------------------------------------
    # ROW 2, COL 2: Top 10 Content Producing Countries
    # ----------------------------------------------------
    ax_country = fig.add_subplot(gs[2, 2])
    style_panel(ax_country, "Top 10 Countries by Content Volume (Type Split)")
    
    top_cntry_df = (
        df[df['primary_country'] != 'Unknown']
        .groupby(['primary_country', 'type'])
        .size()
        .unstack(fill_value=0)
    )
    top_cntry_df['Total'] = top_cntry_df['Movie'] + top_cntry_df.get('TV Show', 0)
    top10_cntry = top_cntry_df.sort_values(by='Total', ascending=True).tail(10)
    
    y_pos = np.arange(len(top10_cntry))
    ax_country.barh(y_pos, top10_cntry['Movie'], color=movie_color, edgecolor='none', height=0.62, label='Movies')
    ax_country.barh(y_pos, top10_cntry['TV Show'], left=top10_cntry['Movie'], color=tv_color, edgecolor='none', height=0.62, label='TV Shows')
    ax_country.set_yticks(y_pos)
    ax_country.set_yticklabels(top10_cntry.index, color=text_primary, fontsize=9)
    ax_country.set_xlabel("Total Titles Available", color=text_secondary, fontsize=9.5, labelpad=8)
    ax_country.grid(True, axis='x', linestyle='--', alpha=0.15, color='#FFFFFF')
    ax_country.legend(facecolor='#222228', edgecolor=border_color, labelcolor=text_primary, fontsize=8.5, loc='lower right')

    # ----------------------------------------------------
    # ROW 3, COL 0: Top 10 Primary Genres
    # ----------------------------------------------------
    ax_genre = fig.add_subplot(gs[3, 0])
    style_panel(ax_genre, "Top 10 Most Represented Primary Genres")
    
    top_genres = df['primary_genre'].value_counts().head(10).sort_values(ascending=True)
    y_g = np.arange(len(top_genres))
    bars = ax_genre.barh(y_g, top_genres.values, color='#6366F1', edgecolor='none', height=0.62)
    ax_genre.set_yticks(y_g)
    ax_genre.set_yticklabels(top_genres.index, color=text_primary, fontsize=9)
    ax_genre.set_xlabel("Number of Titles", color=text_secondary, fontsize=9.5, labelpad=8)
    ax_genre.grid(True, axis='x', linestyle='--', alpha=0.15, color='#FFFFFF')
    
    # Add data labels
    for bar in bars:
        w = bar.get_width()
        ax_genre.text(w + 15, bar.get_y() + bar.get_height()/2, f"{int(w):,}",
                      ha='left', va='center', color=text_secondary, fontsize=8.5)
    ax_genre.set_xlim(0, max(top_genres.values) * 1.15)

    # ----------------------------------------------------
    # ROW 3, COL 1: Movie Duration Distribution (Histogram)
    # ----------------------------------------------------
    ax_hist = fig.add_subplot(gs[3, 1])
    style_panel(ax_hist, "Movie Runtime Distribution (Minutes)")
    
    movie_durations = df[df['type'] == 'Movie']['duration_minutes'].dropna()
    sns.histplot(movie_durations, bins=35, kde=True, ax=ax_hist, color=movie_color, alpha=0.65, edgecolor='#18181C')
    
    mean_val = movie_durations.mean()
    ax_hist.axvline(mean_val, color='#FBBF24', linestyle='--', linewidth=2, label=f'Mean: {mean_val:.1f} min')
    ax_hist.set_xlabel("Runtime (Minutes)", color=text_secondary, fontsize=9.5, labelpad=8)
    ax_hist.set_ylabel("Frequency of Movies", color=text_secondary, fontsize=9.5, labelpad=8)
    ax_hist.grid(True, linestyle='--', alpha=0.15, color='#FFFFFF')
    ax_hist.legend(facecolor='#222228', edgecolor=border_color, labelcolor=text_primary, fontsize=8.5, loc='upper right')

    # ----------------------------------------------------
    # ROW 3, COL 2: TV Show Longevity & Content Ratings Split
    # ----------------------------------------------------
    ax_tv = fig.add_subplot(gs[3, 2])
    style_panel(ax_tv, "TV Show Longevity (Season Count Distribution)")
    
    season_counts = df[df['type'] == 'TV Show']['duration_seasons'].value_counts().sort_index()
    # Group 5+ seasons
    s1 = season_counts.get(1, 0)
    s2 = season_counts.get(2, 0)
    s3 = season_counts.get(3, 0)
    s4 = season_counts.get(4, 0)
    s5_plus = season_counts[season_counts.index >= 5].sum()
    
    s_labels = ['1 Season', '2 Seasons', '3 Seasons', '4 Seasons', '5+ Seasons']
    s_vals = [s1, s2, s3, s4, s5_plus]
    s_pcts = [v / sum(s_vals) * 100 for v in s_vals]
    
    x_s = np.arange(len(s_labels))
    bars_s = ax_tv.bar(x_s, s_vals, color=tv_color, edgecolor='none', width=0.55)
    ax_tv.set_xticks(x_s)
    ax_tv.set_xticklabels(s_labels, color=text_primary, fontsize=9)
    ax_tv.set_ylabel("Number of TV Shows", color=text_secondary, fontsize=9.5, labelpad=8)
    ax_tv.grid(True, axis='y', linestyle='--', alpha=0.15, color='#FFFFFF')
    
    for bar, pct in zip(bars_s, s_pcts):
        h = bar.get_height()
        ax_tv.text(bar.get_x() + bar.get_width()/2, h + 30, f"{int(h):,}\n({pct:.1f}%)",
                   ha='center', va='bottom', color=text_primary, fontsize=8.5, fontweight='medium')
    ax_tv.set_ylim(0, max(s_vals) * 1.18)

    # Save finalized dashboard image
    print(f"Rendering high-resolution executive dashboard to: {out_path}...")
    plt.savefig(out_path, dpi=150, facecolor=bg_color, bbox_inches='tight')
    plt.close()
    print("Successfully generated Dashboard/netflix_dashboard.png!")

if __name__ == '__main__':
    generate_dashboard()
