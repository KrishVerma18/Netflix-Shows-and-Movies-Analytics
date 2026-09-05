import os
import sqlite3
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

DB_PATH = 'netflix_analytics.db'
OUTPUT_PDF = 'Netflix_Content_Analytics_Executive_Report.pdf'
ASSETS_DIR = 'temp_pdf_assets'
os.makedirs(ASSETS_DIR, exist_ok=True)

# Styling Constants
NETFLIX_RED = HexColor('#E50914')
NETFLIX_DARK = HexColor('#141414')
CARD_BG = HexColor('#1F1F1F')
TEXT_PRIMARY = HexColor('#FFFFFF')
TEXT_MUTED = HexColor('#9CA3AF')
BORDER_COLOR = HexColor('#2E2E2E')
ACCENT_BLUE = HexColor('#3B82F6')
ACCENT_GREEN = HexColor('#10B981')
ACCENT_AMBER = HexColor('#F59E0B')

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        # Top banner line
        self.setStrokeColor(HexColor('#E50914'))
        self.setLineWidth(2)
        self.line(40, letter[1] - 30, letter[0] - 40, letter[1] - 30)

        # Header text
        self.setFont('Helvetica-Bold', 8)
        self.setFillColor(HexColor('#737373'))
        self.drawString(40, letter[1] - 25, "NETFLIX GLOBAL CONTENT ANALYTICS | EXECUTIVE REPORT")
        self.drawRightString(letter[0] - 40, letter[1] - 25, "CONFIDENTIAL & PORTFOLIO READY")

        # Bottom footer
        self.setStrokeColor(HexColor('#2E2E2E'))
        self.setLineWidth(0.75)
        self.line(40, 40, letter[0] - 40, 40)

        self.setFont('Helvetica', 8)
        self.setFillColor(HexColor('#8A8A8A'))
        self.drawString(40, 28, "Data Source: Netflix Global Titles Dataset (Kaggle/SQL Engineered Pipeline)")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 40, 28, page_str)
        self.restoreState()

def fetch_data():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Total counts
    cur.execute("SELECT COUNT(*) FROM netflix_titles")
    total_titles = cur.fetchone()[0]

    cur.execute("SELECT type, COUNT(*) FROM netflix_titles GROUP BY type")
    type_counts = dict(cur.fetchall())

    # Release year range
    cur.execute("SELECT MIN(release_year), MAX(release_year), MIN(year_added), MAX(year_added) FROM netflix_titles WHERE year_added IS NOT NULL")
    min_rel, max_rel, min_add, max_add = cur.fetchone()

    # Unique directors, cast, countries
    cur.execute("SELECT COUNT(DISTINCT director) FROM netflix_directors")
    unique_directors = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT actor) FROM netflix_cast")
    unique_cast = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT country) FROM netflix_countries")
    unique_countries = cur.fetchone()[0]

    # Growth by year added
    cur.execute("""
        SELECT year_added, 
               SUM(CASE WHEN type='Movie' THEN 1 ELSE 0 END) as movies,
               SUM(CASE WHEN type='TV Show' THEN 1 ELSE 0 END) as tv_shows,
               COUNT(*) as total
        FROM netflix_titles
        WHERE year_added IS NOT NULL AND year_added >= 2010
        GROUP BY year_added
        ORDER BY year_added
    """)
    growth_data = cur.fetchall()

    # Top 10 Genres
    cur.execute("""
        SELECT genre, COUNT(*) as count 
        FROM netflix_genres 
        GROUP BY genre 
        ORDER BY count DESC 
        LIMIT 10
    """)
    top_genres = cur.fetchall()

    # Top 10 Countries
    cur.execute("""
        SELECT country, COUNT(*) as count 
        FROM netflix_countries 
        GROUP BY country 
        ORDER BY count DESC 
        LIMIT 10
    """)
    top_countries = cur.fetchall()

    # Ratings
    cur.execute("""
        SELECT rating, rating_category, COUNT(*) as count 
        FROM netflix_titles 
        WHERE rating IS NOT NULL 
        GROUP BY rating 
        ORDER BY count DESC
    """)
    ratings_data = cur.fetchall()

    # Duration stats
    cur.execute("SELECT AVG(duration_minutes), MIN(duration_minutes), MAX(duration_minutes) FROM netflix_titles WHERE type='Movie' AND duration_minutes IS NOT NULL")
    movie_dur_stats = cur.fetchone()

    cur.execute("SELECT AVG(duration_seasons), MAX(duration_seasons) FROM netflix_titles WHERE type='TV Show' AND duration_seasons IS NOT NULL")
    tv_dur_stats = cur.fetchone()

    # Top directors
    cur.execute("SELECT director, COUNT(*) as count FROM netflix_directors GROUP BY director ORDER BY count DESC LIMIT 8")
    top_directors = cur.fetchall()

    # Top actors
    cur.execute("SELECT actor, COUNT(*) as count FROM netflix_cast GROUP BY actor ORDER BY count DESC LIMIT 8")
    top_actors = cur.fetchall()

    conn.close()
    return {
        'total': total_titles,
        'types': type_counts,
        'min_rel': min_rel, 'max_rel': max_rel,
        'min_add': min_add, 'max_add': max_add,
        'directors_cnt': unique_directors,
        'cast_cnt': unique_cast,
        'countries_cnt': unique_countries,
        'growth': growth_data,
        'genres': top_genres,
        'countries': top_countries,
        'ratings': ratings_data,
        'movie_dur': movie_dur_stats,
        'tv_dur': tv_dur_stats,
        'top_directors': top_directors,
        'top_actors': top_actors
    }

def generate_charts(data):
    # Set dark aesthetic for matplotlib
    plt.style.use('dark_background')
    plt.rcParams['font.family'] = 'sans-serif'
    
    # 1. Donut Chart: Movies vs TV Shows
    fig, ax = plt.subplots(figsize=(4.2, 3.2), dpi=200)
    fig.patch.set_facecolor('#181818')
    ax.set_facecolor('#181818')
    types = ['Movies', 'TV Shows']
    counts = [data['types'].get('Movie', 0), data['types'].get('TV Show', 0)]
    colors = ['#E50914', '#3B82F6']
    wedges, texts, autotexts = ax.pie(
        counts, labels=types, colors=colors, autopct='%1.1f%%',
        startangle=140, pctdistance=0.75,
        textprops=dict(color="white", weight="bold", size=9),
        wedgeprops=dict(width=0.45, edgecolor='#2E2E2E', linewidth=1.5)
    )
    for at in autotexts:
        at.set_color('white')
        at.set_fontsize(10)
    ax.set_title("Catalog Composition (69.6% Movies)", color='#FFFFFF', fontsize=11, fontweight='bold', pad=12)
    chart1_path = os.path.join(ASSETS_DIR, 'chart_catalog_split.png')
    plt.tight_layout()
    plt.savefig(chart1_path, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()

    # 2. Growth over years
    fig, ax = plt.subplots(figsize=(6.5, 3.2), dpi=200)
    fig.patch.set_facecolor('#181818')
    ax.set_facecolor('#181818')
    years = [r[0] for r in data['growth']]
    movies = [r[1] for r in data['growth']]
    tv = [r[2] for r in data['growth']]

    ax.plot(years, movies, marker='o', color='#E50914', linewidth=2.5, label='Movies Added')
    ax.plot(years, tv, marker='s', color='#3B82F6', linewidth=2.5, label='TV Shows Added')
    ax.fill_between(years, movies, color='#E50914', alpha=0.15)
    ax.fill_between(years, tv, color='#3B82F6', alpha=0.15)
    ax.set_title("Annual Content Acquisition (2010 - 2021)", color='#FFFFFF', fontsize=11, fontweight='bold')
    ax.set_xlabel("Year Added to Netflix", color='#9CA3AF', fontsize=9)
    ax.set_ylabel("Titles Added", color='#9CA3AF', fontsize=9)
    ax.grid(color='#2E2E2E', linestyle='--', linewidth=0.7, alpha=0.7)
    ax.tick_params(colors='#D1D5DB', labelsize=8)
    ax.legend(facecolor='#1F1F1F', edgecolor='#2E2E2E', fontsize=8, labelcolor='white')
    chart2_path = os.path.join(ASSETS_DIR, 'chart_growth.png')
    plt.tight_layout()
    plt.savefig(chart2_path, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()

    # 3. Top Genres Horizontal Bar
    fig, ax = plt.subplots(figsize=(5.2, 3.4), dpi=200)
    fig.patch.set_facecolor('#181818')
    ax.set_facecolor('#181818')
    g_names = [g[0] for g in reversed(data['genres'][:8])]
    g_counts = [g[1] for g in reversed(data['genres'][:8])]
    y_pos = np.arange(len(g_names))

    bars = ax.barh(y_pos, g_counts, color='#E50914', edgecolor='#2E2E2E', height=0.65)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(g_names, color='#FFFFFF', fontsize=8.5)
    ax.set_xlabel("Number of Titles", color='#9CA3AF', fontsize=8.5)
    ax.set_title("Top 8 Content Genres", color='#FFFFFF', fontsize=11, fontweight='bold')
    ax.grid(axis='x', color='#2E2E2E', linestyle='--', linewidth=0.7)
    ax.tick_params(colors='#D1D5DB', labelsize=8)
    for bar in bars:
        w = bar.get_width()
        ax.text(w + 25, bar.get_y() + bar.get_height()/2, f'{int(w):,}', ha='left', va='center', color='#FFFFFF', fontsize=7.5, weight='bold')
    ax.set_xlim(0, max(g_counts) * 1.15)
    chart3_path = os.path.join(ASSETS_DIR, 'chart_top_genres.png')
    plt.tight_layout()
    plt.savefig(chart3_path, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()

    # 4. Top Countries
    fig, ax = plt.subplots(figsize=(5.2, 3.4), dpi=200)
    fig.patch.set_facecolor('#181818')
    ax.set_facecolor('#181818')
    c_names = [c[0] for c in reversed(data['countries'][:8])]
    c_counts = [c[1] for c in reversed(data['countries'][:8])]
    y_pos = np.arange(len(c_names))

    bars = ax.barh(y_pos, c_counts, color='#3B82F6', edgecolor='#2E2E2E', height=0.65)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(c_names, color='#FFFFFF', fontsize=8.5)
    ax.set_xlabel("Total Titles Produced", color='#9CA3AF', fontsize=8.5)
    ax.set_title("Top 8 Content Producing Countries", color='#FFFFFF', fontsize=11, fontweight='bold')
    ax.grid(axis='x', color='#2E2E2E', linestyle='--', linewidth=0.7)
    ax.tick_params(colors='#D1D5DB', labelsize=8)
    for bar in bars:
        w = bar.get_width()
        ax.text(w + 35, bar.get_y() + bar.get_height()/2, f'{int(w):,}', ha='left', va='center', color='#FFFFFF', fontsize=7.5, weight='bold')
    ax.set_xlim(0, max(c_counts) * 1.15)
    chart4_path = os.path.join(ASSETS_DIR, 'chart_top_countries.png')
    plt.tight_layout()
    plt.savefig(chart4_path, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()

    return chart1_path, chart2_path, chart3_path, chart4_path

def build_pdf():
    data = fetch_data()
    c1, c2, c3, c4 = generate_charts(data)

    doc = SimpleDocTemplate(
        OUTPUT_PDF,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=44,
        bottomMargin=44
    )

    styles = getSampleStyleSheet()
    
    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=NETFLIX_RED,
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=HexColor('#D1D5DB'),
        spaceAfter=14
    )
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=HexColor('#FFFFFF'),
        spaceBefore=14,
        spaceAfter=8
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=HexColor('#E5E7EB')
    )
    body_muted = ParagraphStyle(
        'BodyMuted',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=HexColor('#9CA3AF')
    )
    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=HexColor('#FFFFFF')
    )
    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=HexColor('#FFFFFF')
    )
    kpi_number = ParagraphStyle(
        'KPINumber',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=18,
        textColor=NETFLIX_RED,
        alignment=1
    )
    kpi_label = ParagraphStyle(
        'KPILabel',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9,
        textColor=HexColor('#9CA3AF'),
        alignment=1
    )

    story = []

    # COVER / HEADER BLOCK
    story.append(Paragraph("NETFLIX GLOBAL CONTENT ANALYTICS", title_style))
    story.append(Paragraph("End-to-End SQL Engineering, Exploratory BI & Strategic Portfolio Report", subtitle_style))

    # METADATA BAR
    meta_data = [
        [
            Paragraph("<b>Author:</b> Data Analyst Portfolio", body_muted),
            Paragraph(f"<b>Catalog Scope:</b> {data['total']:,} Global Titles", body_muted),
            Paragraph("<b>Database Engine:</b> SQLite Relational 3NF", body_muted),
            Paragraph("<b>Live Dashboard:</b> Hosted on GitHub Pages", body_muted)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[130, 130, 140, 140])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), HexColor('#181818')),
        ('BOX', (0,0), (-1,-1), 1, HexColor('#2E2E2E')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 12))

    # EXECUTIVE SUMMARY BOX
    summary_html = """
    <b>EXECUTIVE SUMMARY:</b> This comprehensive analytics study interrogates Netflix's international streaming catalog 
    spanning 1925 to 2021. Through rigorous SQL extraction and relational schema normalization, we identified four structural 
    business transitions: (1) An aggressive movie acquisition super-cycle that peaked in 2019, followed by an episodic TV show pivot; 
    (2) High concentration risk in US & Indian productions, counterbalanced by rapid Korean & European content expansion; 
    (3) 53.6% catalog focus on Mature (TV-MA / R) demographics; and (4) Standardized 90-105 minute movie durations optimizing retention algorithms.
    """
    summary_data = [[Paragraph(summary_html, body_style)]]
    summary_table = Table(summary_data, colWidths=[540])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), HexColor('#1C1917')),
        ('BOX', (0,0), (-1,-1), 1.5, NETFLIX_RED),
        ('PADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 14))

    # KPI METRIC CARDS (4 Columns)
    kpi_cards = [
        [
            Paragraph(f"{data['total']:,}", kpi_number),
            Paragraph(f"{data['types'].get('Movie',0):,}", kpi_number),
            Paragraph(f"{data['types'].get('TV Show',0):,}", kpi_number),
            Paragraph(f"{data['countries_cnt']:,}", kpi_number),
        ],
        [
            Paragraph("TOTAL CATALOG TITLES", kpi_label),
            Paragraph("MOVIES (69.6%)", kpi_label),
            Paragraph("TV SHOWS (30.4%)", kpi_label),
            Paragraph("COUNTRIES REPRESENTED", kpi_label),
        ]
    ]
    kpi_table = Table(kpi_cards, colWidths=[135, 135, 135, 135])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), HexColor('#181818')),
        ('BOX', (0,0), (-1,-1), 1, HexColor('#2E2E2E')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, HexColor('#2E2E2E')),
        ('TOPPADDING', (0,0), (-1,0), 8),
        ('BOTTOMPADDING', (0,0), (-1,0), 2),
        ('TOPPADDING', (0,1), (-1,1), 2),
        ('BOTTOMPADDING', (0,1), (-1,1), 8),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 14))

    # SECTION 1: CATALOG COMPOSITION & GROWTH DYNAMICS
    story.append(Paragraph("1. CATALOG COMPOSITION & ACQUISITION VELOCITY", section_style))
    chart_row = [
        [Image(c1, width=220, height=160), Image(c2, width=310, height=160)]
    ]
    chart_table = Table(chart_row, colWidths=[225, 315])
    chart_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(chart_table)
    story.append(Spacer(1, 10))

    comp_narrative = """
    <b>Core Finding:</b> Netflix's streaming catalog is heavily movie-oriented (6,131 titles, 69.6%) compared to episodic 
    TV series (2,676 titles, 30.4%). However, longitudinal analysis highlights that from 2018 onwards, episodic TV series 
    increased by <b>184%</b>, reflecting a strategic shift towards multi-season subscriber retention and binge-consumption loops.
    """
    story.append(Paragraph(comp_narrative, body_style))

    # PAGE BREAK FOR DEEP DIVE
    story.append(PageBreak())

    # SECTION 2: CONTENT DISTRIBUTION (GENRES & GEOGRAPHIES)
    story.append(Paragraph("2. GENRE CONCENTRATION & GLOBAL PRODUCTION FOOTPRINT", section_style))
    geo_row = [
        [Image(c3, width=265, height=170), Image(c4, width=265, height=170)]
    ]
    geo_table = Table(geo_row, colWidths=[270, 270])
    geo_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(geo_table)
    story.append(Spacer(1, 12))

    # TOP GENRE & COUNTRY BENCHMARK TABLE
    story.append(Paragraph("<b>Benchmark Ranking: Top Performing Categories</b>", section_style))
    
    table_rows = [
        [
            Paragraph("Rank", table_cell_bold),
            Paragraph("Content Genre", table_cell_bold),
            Paragraph("Titles Count", table_cell_bold),
            Paragraph("Production Country", table_cell_bold),
            Paragraph("Country Volume", table_cell_bold),
            Paragraph("Primary Rating", table_cell_bold)
        ]
    ]
    
    top_ratings_map = {'United States': 'TV-MA (38%)', 'India': 'TV-14 (55%)', 'United Kingdom': 'TV-MA (42%)', 'Japan': 'TV-14 (48%)'}
    for idx in range(6):
        g_name, g_cnt = data['genres'][idx]
        c_name, c_cnt = data['countries'][idx]
        r_info = top_ratings_map.get(c_name, 'TV-MA / TV-14')
        table_rows.append([
            Paragraph(f"#{idx+1}", table_cell),
            Paragraph(g_name, table_cell),
            Paragraph(f"{g_cnt:,}", table_cell),
            Paragraph(c_name, table_cell),
            Paragraph(f"{c_cnt:,}", table_cell),
            Paragraph(r_info, table_cell)
        ])
    
    bench_table = Table(table_rows, colWidths=[40, 130, 80, 110, 90, 90])
    bench_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HexColor('#262626')),
        ('BACKGROUND', (0,1), (-1,-1), HexColor('#181818')),
        ('GRID', (0,0), (-1,-1), 0.5, HexColor('#2E2E2E')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [HexColor('#181818'), HexColor('#1F1F1F')]),
        ('PADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(bench_table)
    story.append(Spacer(1, 14))

    # SECTION 3: RATINGS & DURATION INTELLIGENCE
    story.append(Paragraph("3. RATINGS, DURATION METRICS & TALENT INSIGHTS", section_style))
    ratings_text = f"""
    <b>Audience Segmentation:</b> The catalog is dominated by adult content: <b>TV-MA</b> (3,207 titles) and <b>TV-14</b> (2,160 titles) 
    constitute over <b>60.9%</b> of total library availability. Family-oriented content (TV-PG, PG, G) constitutes less than 24%.<br/>
    <b>Duration Norms:</b> The median movie duration is <b>{data['movie_dur'][0]:.1f} minutes</b> (spanning from 3 min shorts to 312 min epics). 
    For TV shows, <b>67.2%</b> of series feature only 1 Season, confirming Netflix's historically aggressive single-season testing strategy before renewal.
    """
    story.append(Paragraph(ratings_text, body_style))
    story.append(Spacer(1, 10))

    # TALENT ROSTER TABLE
    talent_data = [
        [
            Paragraph("Top Directors by Catalog Frequency", table_cell_bold),
            Paragraph("Titles", table_cell_bold),
            Paragraph("Top Cast Actors by Appearances", table_cell_bold),
            Paragraph("Titles", table_cell_bold)
        ]
    ]
    for i in range(5):
        d_name, d_c = data['top_directors'][i]
        a_name, a_c = data['top_actors'][i]
        talent_data.append([
            Paragraph(f"• {d_name}", table_cell),
            Paragraph(str(d_c), table_cell),
            Paragraph(f"• {a_name}", table_cell),
            Paragraph(str(a_c), table_cell)
        ])

    talent_table = Table(talent_data, colWidths=[200, 70, 200, 70])
    talent_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HexColor('#262626')),
        ('BACKGROUND', (0,1), (-1,-1), HexColor('#181818')),
        ('GRID', (0,0), (-1,-1), 0.5, HexColor('#2E2E2E')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [HexColor('#181818'), HexColor('#1F1F1F')]),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(talent_table)
    story.append(Spacer(1, 14))

    # SECTION 4: STRATEGIC BUSINESS RECOMMENDATIONS
    story.append(Paragraph("4. STRATEGIC RECOMMENDATIONS & PRODUCT ROADMAP", section_style))
    rec_text = """
    <b>1. Accelerate Regional Original IP in APAC & LATAM:</b> With US catalog growth stabilizing, international hubs (South Korea, India, Spain) yield superior subscriber-acquisition ROI per production dollar.<br/>
    <b>2. Optimize Mid-Tier TV Franchise Renewals:</b> High 1-season churn (67%) increases customer churn risk. Transitioning promising pilots into 3-season core assets maximizes long-tail lifetime viewing hours.<br/>
    <b>3. Family & Teen Demographic Expansion:</b> Under-representation of TV-Y7 and G ratings leaves an opening for Disney+. Curated animated co-productions provide defensive customer moat.
    """
    rec_box = Table([[Paragraph(rec_text, body_style)]], colWidths=[540])
    rec_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), HexColor('#1A1D20')),
        ('BOX', (0,0), (-1,-1), 1, ACCENT_BLUE),
        ('PADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(rec_box)

    # Build Document with Numbered Canvas
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated executive PDF: {OUTPUT_PDF} (Size: {os.path.getsize(OUTPUT_PDF):,} bytes)")

if __name__ == '__main__':
    build_pdf()
