"""
Netflix Shows & Movies Analytics - PDF Report Generator
Generates a professional analytics report from the SQLite database
"""

import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'netflix_analytics.db')

def fetch_data():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    data = {}

    # 1. Overview stats
    c.execute("SELECT COUNT(*) as total FROM netflix_titles")
    data['total'] = c.fetchone()['total']

    c.execute("SELECT COUNT(*) as movies FROM netflix_titles WHERE type='Movie'")
    data['movies'] = c.fetchone()['movies']

    c.execute("SELECT COUNT(*) as shows FROM netflix_titles WHERE type='TV Show'")
    data['shows'] = c.fetchone()['shows']

    c.execute("SELECT COUNT(DISTINCT primary_country) as countries FROM netflix_titles WHERE primary_country IS NOT NULL AND primary_country != ''")
    data['countries'] = c.fetchone()['countries']

    c.execute("SELECT MIN(release_year) as min_yr, MAX(release_year) as max_yr FROM netflix_titles WHERE release_year IS NOT NULL")
    row = c.fetchone()
    data['min_year'] = row['min_yr']
    data['max_year'] = row['max_yr']

    # 2. Content by year added
    c.execute("""
        SELECT year_added, COUNT(*) as cnt
        FROM netflix_titles
        WHERE year_added IS NOT NULL AND year_added >= 2015
        GROUP BY year_added
        ORDER BY year_added
    """)
    data['by_year'] = [dict(r) for r in c.fetchall()]

    # 3. Top genres
    c.execute("""
        SELECT primary_genre, COUNT(*) as cnt
        FROM netflix_titles
        WHERE primary_genre IS NOT NULL AND primary_genre != ''
        GROUP BY primary_genre
        ORDER BY cnt DESC
        LIMIT 10
    """)
    rows = c.fetchall()
    data['top_genres'] = [{'genre_primary': r['primary_genre'], 'cnt': r['cnt']} for r in rows]

    # 4. Top countries
    c.execute("""
        SELECT primary_country, COUNT(*) as cnt
        FROM netflix_titles
        WHERE primary_country IS NOT NULL AND primary_country != ''
        GROUP BY primary_country
        ORDER BY cnt DESC
        LIMIT 10
    """)
    rows = c.fetchall()
    data['top_countries'] = [{'country_primary': r['primary_country'], 'cnt': r['cnt']} for r in rows]

    # 5. Rating distribution
    c.execute("""
        SELECT rating, COUNT(*) as cnt
        FROM netflix_titles
        WHERE rating IS NOT NULL AND rating NOT LIKE '%min%'
        GROUP BY rating
        ORDER BY cnt DESC
        LIMIT 10
    """)
    data['ratings'] = [dict(r) for r in c.fetchall()]

    # 6. Top directors
    c.execute("""
        SELECT director, COUNT(*) as cnt
        FROM netflix_titles
        WHERE director IS NOT NULL AND director != '' AND director != 'Unknown'
        GROUP BY director
        ORDER BY cnt DESC
        LIMIT 10
    """)
    rows = c.fetchall()
    data['top_directors'] = [{'director_primary': r['director'], 'cnt': r['cnt']} for r in rows]

    # 7. Movies vs TV ratio by year
    c.execute("""
        SELECT year_added, type, COUNT(*) as cnt
        FROM netflix_titles
        WHERE year_added IS NOT NULL AND year_added >= 2015
        GROUP BY year_added, type
        ORDER BY year_added
    """)
    rows = c.fetchall()
    yr_type = {}
    for r in rows:
        yr = r['year_added']
        if yr not in yr_type:
            yr_type[yr] = {'Movie': 0, 'TV Show': 0}
        yr_type[yr][r['type']] = r['cnt']
    data['by_year_type'] = yr_type

    # 8. Avg movie duration
    c.execute("""
        SELECT AVG(duration_minutes) as avg_dur
        FROM netflix_titles
        WHERE type='Movie' AND duration_minutes IS NOT NULL AND duration_minutes > 0
    """)
    row = c.fetchone()
    data['avg_duration'] = round(row['avg_dur'], 1) if row['avg_dur'] else 'N/A'

    # 9. Recent additions (last 5)
    c.execute("""
        SELECT title, type, primary_country, release_year, rating, primary_genre
        FROM netflix_titles
        WHERE date_added IS NOT NULL
        ORDER BY date_added DESC
        LIMIT 8
    """)
    rows = c.fetchall()
    data['recent'] = [{'title': r['title'], 'type': r['type'], 'country_primary': r['primary_country'],
                       'release_year': r['release_year'], 'rating': r['rating'], 'genre_primary': r['primary_genre']} for r in rows]

    conn.close()
    return data

def generate_html_report(data):
    by_year_rows = ""
    for yr in data['by_year']:
        movies = data['by_year_type'].get(yr['year_added'], {}).get('Movie', 0)
        shows = data['by_year_type'].get(yr['year_added'], {}).get('TV Show', 0)
        by_year_rows += f"<tr><td>{yr['year_added']}</td><td>{yr['cnt']}</td><td>{movies}</td><td>{shows}</td></tr>"

    genre_rows = ""
    for i, g in enumerate(data['top_genres'], 1):
        pct = round(g['cnt'] / data['total'] * 100, 1)
        bar_w = round(g['cnt'] / data['top_genres'][0]['cnt'] * 100)
        genre_rows += f"""
        <tr>
            <td>{i}</td>
            <td><strong>{g['genre_primary']}</strong></td>
            <td>{g['cnt']:,}</td>
            <td>{pct}%</td>
            <td><div class="bar-cell"><div class="bar-fill" style="width:{bar_w}%"></div></div></td>
        </tr>"""

    country_rows = ""
    for i, c in enumerate(data['top_countries'], 1):
        pct = round(c['cnt'] / data['total'] * 100, 1)
        bar_w = round(c['cnt'] / data['top_countries'][0]['cnt'] * 100)
        country_rows += f"""
        <tr>
            <td>{i}</td>
            <td><strong>{c['country_primary']}</strong></td>
            <td>{c['cnt']:,}</td>
            <td>{pct}%</td>
            <td><div class="bar-cell"><div class="bar-fill" style="width:{bar_w}%"></div></div></td>
        </tr>"""

    rating_rows = ""
    for r in data['ratings']:
        pct = round(r['cnt'] / data['total'] * 100, 1)
        rating_rows += f"<tr><td><span class='badge'>{r['rating']}</span></td><td>{r['cnt']:,}</td><td>{pct}%</td></tr>"

    director_rows = ""
    for i, d in enumerate(data['top_directors'], 1):
        director_rows += f"<tr><td>{i}</td><td><strong>{d['director_primary']}</strong></td><td>{d['cnt']}</td></tr>"

    recent_rows = ""
    for r in data['recent']:
        badge_class = "badge-movie" if r['type'] == 'Movie' else "badge-show"
        recent_rows += f"""
        <tr>
            <td>{r['title'][:40]}{'...' if len(r.get('title','')) > 40 else ''}</td>
            <td><span class="badge {badge_class}">{r['type']}</span></td>
            <td>{r.get('country_primary','N/A') or 'N/A'}</td>
            <td>{r.get('release_year','N/A')}</td>
            <td><span class="badge">{r.get('rating','N/A') or 'N/A'}</span></td>
        </tr>"""

    movies_pct = round(data['movies'] / data['total'] * 100, 1)
    shows_pct = round(data['shows'] / data['total'] * 100, 1)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Netflix Content Analytics - Full Report</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    
    :root {{
      --red: #E50914;
      --dark-red: #B20710;
      --black: #0A0A0A;
      --dark: #141414;
      --surface: #1A1A1A;
      --surface2: #222222;
      --border: #2A2A2A;
      --text: #FFFFFF;
      --muted: #A3A3A3;
      --accent: #E50914;
    }}

    @media print {{
      body {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
      .page-break {{ page-break-before: always; }}
      .no-break {{ page-break-inside: avoid; }}
    }}

    html, body {{
      font-family: 'Inter', -apple-system, sans-serif;
      background: #0A0A0A;
      color: #FFFFFF;
      font-size: 13px;
      line-height: 1.6;
    }}

    /* ======= COVER PAGE ======= */
    .cover {{
      min-height: 100vh;
      background: linear-gradient(135deg, #0A0A0A 0%, #1a0000 50%, #0A0A0A 100%);
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      text-align: center;
      padding: 60px 40px;
      position: relative;
      overflow: hidden;
    }}
    .cover::before {{
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0; bottom: 0;
      background: 
        radial-gradient(ellipse 80% 60% at 50% 0%, rgba(229,9,20,0.15) 0%, transparent 70%),
        radial-gradient(ellipse 60% 40% at 50% 100%, rgba(229,9,20,0.08) 0%, transparent 70%);
    }}
    .cover-content {{ position: relative; z-index: 1; }}
    .n-logo {{
      width: 60px; height: 90px; margin: 0 auto 32px;
    }}
    .cover h1 {{
      font-size: 52px;
      font-weight: 800;
      letter-spacing: -1px;
      line-height: 1.1;
      margin-bottom: 16px;
    }}
    .cover h1 span {{ color: #E50914; }}
    .cover-subtitle {{
      font-size: 18px;
      color: #A3A3A3;
      margin-bottom: 48px;
      font-weight: 300;
    }}
    .cover-stats {{
      display: flex;
      gap: 40px;
      justify-content: center;
      flex-wrap: wrap;
      margin-bottom: 48px;
    }}
    .cover-stat {{
      text-align: center;
    }}
    .cover-stat-num {{
      font-size: 36px;
      font-weight: 800;
      color: #E50914;
      display: block;
    }}
    .cover-stat-label {{
      font-size: 12px;
      color: #A3A3A3;
      text-transform: uppercase;
      letter-spacing: 1px;
    }}
    .cover-divider {{
      width: 60px;
      height: 3px;
      background: #E50914;
      margin: 32px auto;
    }}
    .cover-meta {{
      font-size: 13px;
      color: #555;
      line-height: 2;
    }}
    .cover-meta strong {{ color: #888; }}

    /* ======= PAGE WRAPPER ======= */
    .report-page {{
      max-width: 900px;
      margin: 0 auto;
      padding: 60px 50px;
    }}

    /* ======= SECTION HEADER ======= */
    .section-header {{
      margin-bottom: 32px;
      padding-bottom: 16px;
      border-bottom: 1px solid #2A2A2A;
    }}
    .section-tag {{
      font-size: 11px;
      font-weight: 600;
      color: #E50914;
      text-transform: uppercase;
      letter-spacing: 2px;
      margin-bottom: 8px;
    }}
    .section-title {{
      font-size: 28px;
      font-weight: 700;
      color: #FFFFFF;
    }}
    .section-desc {{
      font-size: 13px;
      color: #A3A3A3;
      margin-top: 8px;
    }}

    /* ======= KPI CARDS ======= */
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
      margin-bottom: 40px;
    }}
    .kpi-card {{
      background: #1A1A1A;
      border: 1px solid #2A2A2A;
      border-radius: 12px;
      padding: 24px 20px;
      text-align: center;
    }}
    .kpi-num {{
      font-size: 32px;
      font-weight: 800;
      color: #E50914;
      display: block;
    }}
    .kpi-label {{
      font-size: 11px;
      color: #A3A3A3;
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-top: 4px;
    }}
    .kpi-sub {{
      font-size: 12px;
      color: #555;
      margin-top: 6px;
    }}

    /* ======= DONUT SUMMARY ======= */
    .split-row {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-bottom: 40px;
    }}
    .stat-box {{
      background: #1A1A1A;
      border: 1px solid #2A2A2A;
      border-radius: 12px;
      padding: 28px 24px;
      display: flex;
      align-items: center;
      gap: 20px;
    }}
    .stat-icon {{
      width: 56px;
      height: 56px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      flex-shrink: 0;
    }}
    .stat-icon.red {{ background: rgba(229,9,20,0.15); }}
    .stat-icon.blue {{ background: rgba(99,179,237,0.15); }}
    .stat-num {{
      font-size: 28px;
      font-weight: 800;
      color: #FFFFFF;
    }}
    .stat-pct {{
      font-size: 14px;
      color: #E50914;
      font-weight: 600;
    }}
    .stat-label {{
      font-size: 12px;
      color: #A3A3A3;
    }}

    /* ======= TABLES ======= */
    .table-wrap {{
      background: #1A1A1A;
      border: 1px solid #2A2A2A;
      border-radius: 12px;
      overflow: hidden;
      margin-bottom: 32px;
    }}
    .table-title {{
      padding: 18px 24px;
      font-size: 14px;
      font-weight: 600;
      color: #FFFFFF;
      border-bottom: 1px solid #2A2A2A;
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .table-title::before {{
      content: '';
      width: 4px;
      height: 18px;
      background: #E50914;
      border-radius: 2px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
    }}
    thead th {{
      background: #141414;
      color: #A3A3A3;
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      padding: 12px 16px;
      text-align: left;
    }}
    tbody tr {{
      border-top: 1px solid #222;
      transition: background 0.2s;
    }}
    tbody tr:nth-child(even) {{
      background: rgba(255,255,255,0.02);
    }}
    tbody td {{
      padding: 12px 16px;
      color: #FFFFFF;
      font-size: 12px;
    }}
    tbody td:first-child {{
      color: #555;
      font-size: 11px;
    }}

    /* ======= BAR CELLS ======= */
    .bar-cell {{
      background: #222;
      border-radius: 4px;
      height: 8px;
      width: 120px;
    }}
    .bar-fill {{
      height: 100%;
      background: linear-gradient(90deg, #E50914, #B20710);
      border-radius: 4px;
    }}

    /* ======= BADGES ======= */
    .badge {{
      display: inline-block;
      padding: 3px 10px;
      border-radius: 20px;
      font-size: 11px;
      font-weight: 600;
      background: #2A2A2A;
      color: #A3A3A3;
    }}
    .badge-movie {{
      background: rgba(229,9,20,0.15);
      color: #E50914;
    }}
    .badge-show {{
      background: rgba(99,179,237,0.15);
      color: #63B3ED;
    }}

    /* ======= INSIGHT CARDS ======= */
    .insight-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-bottom: 32px;
    }}
    .insight-card {{
      background: #1A1A1A;
      border: 1px solid #2A2A2A;
      border-radius: 12px;
      padding: 24px;
    }}
    .insight-card.highlight {{
      border-color: rgba(229,9,20,0.4);
      background: rgba(229,9,20,0.05);
    }}
    .insight-title {{
      font-size: 12px;
      font-weight: 600;
      color: #E50914;
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-bottom: 12px;
    }}
    .insight-text {{
      font-size: 13px;
      color: #CCCCCC;
      line-height: 1.7;
    }}

    /* ======= SQL SECTION ======= */
    .sql-block {{
      background: #0D1117;
      border: 1px solid #2A2A2A;
      border-left: 3px solid #E50914;
      border-radius: 8px;
      padding: 20px 24px;
      margin-bottom: 20px;
      font-family: 'Consolas', 'Monaco', monospace;
      font-size: 12px;
      line-height: 1.7;
      color: #e6edf3;
      overflow: hidden;
    }}
    .sql-comment {{ color: #8b949e; }}
    .sql-keyword {{ color: #ff7b72; font-weight: 600; }}
    .sql-func {{ color: #d2a8ff; }}
    .sql-string {{ color: #a5d6ff; }}
    .sql-num {{ color: #79c0ff; }}

    /* ======= FOOTER ======= */
    .report-footer {{
      background: #141414;
      border-top: 1px solid #2A2A2A;
      padding: 40px 50px;
      text-align: center;
      color: #555;
      font-size: 12px;
      line-height: 2;
    }}
    .report-footer strong {{ color: #888; }}
    .footer-logo {{
      font-size: 24px;
      font-weight: 800;
      color: #E50914;
      margin-bottom: 16px;
    }}

    /* ======= PAGE BREAK DIVIDER ======= */
    .pg-divider {{
      border: none;
      border-top: 1px solid #2A2A2A;
      margin: 60px 0;
    }}

    /* ======= TECH STACK ======= */
    .tech-grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
      margin-bottom: 32px;
    }}
    .tech-card {{
      background: #1A1A1A;
      border: 1px solid #2A2A2A;
      border-radius: 10px;
      padding: 20px 16px;
      text-align: center;
    }}
    .tech-icon {{ font-size: 28px; margin-bottom: 8px; }}
    .tech-name {{ font-size: 13px; font-weight: 600; color: #FFFFFF; }}
    .tech-desc {{ font-size: 11px; color: #555; margin-top: 4px; }}
  </style>
</head>
<body>

<!-- ============================= COVER PAGE ============================= -->
<div class="cover">
  <div class="cover-content">
    <svg class="n-logo" viewBox="0 0 60 90" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M0 0H16.5V90H0V0Z" fill="#E50914"/>
      <path d="M43.5 0H60V90H43.5V0Z" fill="#E50914"/>
      <path d="M16.5 0L43.5 90H60L33 0H16.5Z" fill="#B20710"/>
      <path d="M0 0L43.5 90H60L16.5 0H0Z" fill="#E50914"/>
    </svg>
    
    <h1>Netflix <span>Content</span><br>Analytics Report</h1>
    <p class="cover-subtitle">A comprehensive analysis of Netflix's global streaming catalog</p>
    
    <div class="cover-divider"></div>
    
    <div class="cover-stats">
      <div class="cover-stat">
        <span class="cover-stat-num">{data['total']:,}</span>
        <span class="cover-stat-label">Total Titles</span>
      </div>
      <div class="cover-stat">
        <span class="cover-stat-num">{data['movies']:,}</span>
        <span class="cover-stat-label">Movies</span>
      </div>
      <div class="cover-stat">
        <span class="cover-stat-num">{data['shows']:,}</span>
        <span class="cover-stat-label">TV Shows</span>
      </div>
      <div class="cover-stat">
        <span class="cover-stat-num">{data['countries']:,}</span>
        <span class="cover-stat-label">Countries</span>
      </div>
    </div>
    
    <div class="cover-divider"></div>
    
    <div class="cover-meta">
      <strong>Dataset Period:</strong> {data['min_year']} – {data['max_year']}<br>
      <strong>Analyst:</strong> Krish Verma &nbsp;|&nbsp; B.Tech Information Technology<br>
      <strong>Tools:</strong> SQL · Python · Excel · JavaScript · Chart.js<br>
      <strong>Report Date:</strong> September 2026
    </div>
  </div>
</div>

<!-- ============================= SECTION 1: EXECUTIVE OVERVIEW ============================= -->
<div class="report-page">
  <div class="section-header">
    <div class="section-tag">Section 01</div>
    <div class="section-title">Executive Overview</div>
    <div class="section-desc">High-level KPIs and catalog composition summary</div>
  </div>

  <div class="kpi-grid no-break">
    <div class="kpi-card">
      <span class="kpi-num">{data['total']:,}</span>
      <div class="kpi-label">Total Titles</div>
      <div class="kpi-sub">Complete catalog</div>
    </div>
    <div class="kpi-card">
      <span class="kpi-num">{data['movies']:,}</span>
      <div class="kpi-label">Movies</div>
      <div class="kpi-sub">{movies_pct}% of catalog</div>
    </div>
    <div class="kpi-card">
      <span class="kpi-num">{data['shows']:,}</span>
      <div class="kpi-label">TV Shows</div>
      <div class="kpi-sub">{shows_pct}% of catalog</div>
    </div>
    <div class="kpi-card">
      <span class="kpi-num">{data['avg_duration']}m</span>
      <div class="kpi-label">Avg Movie Duration</div>
      <div class="kpi-sub">Minutes per film</div>
    </div>
  </div>

  <div class="split-row no-break">
    <div class="stat-box">
      <div class="stat-icon red">🎬</div>
      <div>
        <div class="stat-num">{data['movies']:,}</div>
        <div class="stat-pct">{movies_pct}% of total</div>
        <div class="stat-label">Movies in catalog</div>
      </div>
    </div>
    <div class="stat-box">
      <div class="stat-icon blue">📺</div>
      <div>
        <div class="stat-num">{data['shows']:,}</div>
        <div class="stat-pct">{shows_pct}% of total</div>
        <div class="stat-label">TV Shows in catalog</div>
      </div>
    </div>
  </div>

  <!-- Content Growth Table -->
  <div class="table-wrap no-break">
    <div class="table-title">Content Growth by Year Added to Netflix</div>
    <table>
      <thead>
        <tr>
          <th>Year</th>
          <th>Total Added</th>
          <th>Movies</th>
          <th>TV Shows</th>
        </tr>
      </thead>
      <tbody>
        {by_year_rows}
      </tbody>
    </table>
  </div>
</div>

<div class="page-break"></div>

<!-- ============================= SECTION 2: GENRE ANALYSIS ============================= -->
<div class="report-page">
  <div class="section-header">
    <div class="section-tag">Section 02</div>
    <div class="section-title">Genre Analysis</div>
    <div class="section-desc">Distribution of content across Netflix's genre taxonomy</div>
  </div>

  <div class="table-wrap no-break">
    <div class="table-title">Top 10 Genres by Content Volume</div>
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Genre</th>
          <th>Titles</th>
          <th>Share</th>
          <th>Volume</th>
        </tr>
      </thead>
      <tbody>
        {genre_rows}
      </tbody>
    </table>
  </div>

  <div class="insight-grid no-break">
    <div class="insight-card highlight">
      <div class="insight-title">🏆 Dominant Genre</div>
      <div class="insight-text">
        <strong>{data['top_genres'][0]['genre_primary']}</strong> is the most prevalent genre on Netflix
        with <strong>{data['top_genres'][0]['cnt']:,} titles</strong> — accounting for
        {round(data['top_genres'][0]['cnt']/data['total']*100,1)}% of the entire catalog.
        This reflects Netflix's strong investment in drama-driven storytelling.
      </div>
    </div>
    <div class="insight-card">
      <div class="insight-title">📊 Genre Diversity</div>
      <div class="insight-text">
        Netflix's top 10 genres span a wide range from {data['top_genres'][0]['genre_primary']}
        to {data['top_genres'][-1]['genre_primary']}, demonstrating a deliberate strategy
        to cater to diverse audience segments and global tastes across different age groups
        and cultural preferences.
      </div>
    </div>
    <div class="insight-card">
      <div class="insight-title">🎭 Genre #2</div>
      <div class="insight-text">
        <strong>{data['top_genres'][1]['genre_primary']}</strong> ranks second with
        <strong>{data['top_genres'][1]['cnt']:,} titles</strong> ({round(data['top_genres'][1]['cnt']/data['total']*100,1)}%),
        suggesting strong audience demand for this genre category on the platform.
      </div>
    </div>
    <div class="insight-card">
      <div class="insight-title">🌍 Global Strategy</div>
      <div class="insight-text">
        The presence of International content genres in the top 10 indicates Netflix's
        intentional strategy to produce and license non-English language content to
        serve global subscribers and drive international subscriber growth.
      </div>
    </div>
  </div>
</div>

<div class="page-break"></div>

<!-- ============================= SECTION 3: GEOGRAPHY ============================= -->
<div class="report-page">
  <div class="section-header">
    <div class="section-tag">Section 03</div>
    <div class="section-title">Geographic Distribution</div>
    <div class="section-desc">Regional content production and licensing analysis</div>
  </div>

  <div class="table-wrap no-break">
    <div class="table-title">Top 10 Content-Producing Countries</div>
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Country</th>
          <th>Titles</th>
          <th>Share</th>
          <th>Volume</th>
        </tr>
      </thead>
      <tbody>
        {country_rows}
      </tbody>
    </table>
  </div>

  <div class="insight-grid no-break">
    <div class="insight-card highlight">
      <div class="insight-title">🇺🇸 US Dominance</div>
      <div class="insight-text">
        The United States leads global content production on Netflix with
        <strong>{data['top_countries'][0]['cnt']:,} titles</strong> 
        ({round(data['top_countries'][0]['cnt']/data['total']*100,1)}% of catalog),
        reflecting Hollywood's historical advantage in content production infrastructure.
      </div>
    </div>
    <div class="insight-card">
      <div class="insight-title">🌏 Asian Content Rise</div>
      <div class="insight-text">
        India and other Asian nations appear prominently in the top 10, reflecting
        Netflix's aggressive expansion into South Asian and East Asian markets
        with both licensed and original content investment.
      </div>
    </div>
    <div class="insight-card">
      <div class="insight-title">🌍 Geographic Reach</div>
      <div class="insight-text">
        Content from <strong>{data['countries']:,} countries</strong> is represented in
        the Netflix catalog, showcasing a truly global content strategy that spans
        multiple continents and diverse cultural backgrounds.
      </div>
    </div>
    <div class="insight-card">
      <div class="insight-title">🤝 Co-productions</div>
      <div class="insight-text">
        International co-productions are a growing trend on Netflix, with many titles
        listing multiple countries as production partners, enabling cross-market appeal
        and shared production costs.
      </div>
    </div>
  </div>
</div>

<div class="page-break"></div>

<!-- ============================= SECTION 4: RATINGS & DIRECTORS ============================= -->
<div class="report-page">
  <div class="section-header">
    <div class="section-tag">Section 04</div>
    <div class="section-title">Ratings & Content Classification</div>
    <div class="section-desc">Age certification distribution and audience targeting analysis</div>
  </div>

  <div class="table-wrap no-break">
    <div class="table-title">Content Rating Distribution</div>
    <table>
      <thead>
        <tr>
          <th>Rating</th>
          <th>Titles</th>
          <th>% of Catalog</th>
        </tr>
      </thead>
      <tbody>
        {rating_rows}
      </tbody>
    </table>
  </div>

  <div class="insight-grid no-break" style="grid-template-columns: 1fr;">
    <div class="insight-card highlight">
      <div class="insight-title">🔞 Maturity Profile Insight</div>
      <div class="insight-text">
        Netflix's content leans toward mature audiences (TV-MA, TV-14, R), which aligns with
        its subscription model — adults with disposable income are the primary subscriber base.
        However, family-friendly content (TV-G, TV-Y, PG) forms a significant segment aimed
        at retaining household subscriptions. This dual-track strategy maximizes catalog
        appeal across age demographics while driving household plan upgrades.
      </div>
    </div>
  </div>

  <hr class="pg-divider">

  <div class="section-header">
    <div class="section-tag">Section 05</div>
    <div class="section-title">Top Directors</div>
    <div class="section-desc">Most prolific directors on the Netflix platform</div>
  </div>

  <div class="table-wrap no-break">
    <div class="table-title">Top 10 Directors by Number of Titles</div>
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Director</th>
          <th>Titles on Netflix</th>
        </tr>
      </thead>
      <tbody>
        {director_rows}
      </tbody>
    </table>
  </div>
</div>

<div class="page-break"></div>

<!-- ============================= SECTION 5: RECENT ADDITIONS ============================= -->
<div class="report-page">
  <div class="section-header">
    <div class="section-tag">Section 06</div>
    <div class="section-title">Recent Catalog Additions</div>
    <div class="section-desc">Latest titles added to the Netflix streaming catalog</div>
  </div>

  <div class="table-wrap no-break">
    <div class="table-title">Most Recently Added Titles</div>
    <table>
      <thead>
        <tr>
          <th>Title</th>
          <th>Type</th>
          <th>Country</th>
          <th>Release Year</th>
          <th>Rating</th>
        </tr>
      </thead>
      <tbody>
        {recent_rows}
      </tbody>
    </table>
  </div>

  <hr class="pg-divider">

  <!-- ============================= SECTION 6: KEY SQL QUERIES ============================= -->
  <div class="section-header">
    <div class="section-tag">Section 07</div>
    <div class="section-title">Key SQL Queries</div>
    <div class="section-desc">Core analytical queries used to derive insights from the database</div>
  </div>

  <div class="sql-block no-break">
    <span class="sql-comment">-- Content Growth Analysis: Titles added per year</span><br>
    <span class="sql-keyword">SELECT</span> year_added,<br>
    &nbsp;&nbsp;&nbsp;&nbsp;<span class="sql-func">COUNT</span>(*) <span class="sql-keyword">AS</span> total_titles,<br>
    &nbsp;&nbsp;&nbsp;&nbsp;<span class="sql-func">SUM</span>(<span class="sql-keyword">CASE WHEN</span> type = <span class="sql-string">'Movie'</span> <span class="sql-keyword">THEN</span> <span class="sql-num">1</span> <span class="sql-keyword">ELSE</span> <span class="sql-num">0</span> <span class="sql-keyword">END</span>) <span class="sql-keyword">AS</span> movies,<br>
    &nbsp;&nbsp;&nbsp;&nbsp;<span class="sql-func">SUM</span>(<span class="sql-keyword">CASE WHEN</span> type = <span class="sql-string">'TV Show'</span> <span class="sql-keyword">THEN</span> <span class="sql-num">1</span> <span class="sql-keyword">ELSE</span> <span class="sql-num">0</span> <span class="sql-keyword">END</span>) <span class="sql-keyword">AS</span> tv_shows<br>
    <span class="sql-keyword">FROM</span> netflix_titles<br>
    <span class="sql-keyword">WHERE</span> year_added <span class="sql-keyword">IS NOT NULL</span><br>
    <span class="sql-keyword">GROUP BY</span> year_added<br>
    <span class="sql-keyword">ORDER BY</span> year_added;
  </div>

  <div class="sql-block no-break">
    <span class="sql-comment">-- Top Genres: Content distribution by primary genre</span><br>
    <span class="sql-keyword">SELECT</span> genre_primary,<br>
    &nbsp;&nbsp;&nbsp;&nbsp;<span class="sql-func">COUNT</span>(*) <span class="sql-keyword">AS</span> title_count,<br>
    &nbsp;&nbsp;&nbsp;&nbsp;<span class="sql-func">ROUND</span>(<span class="sql-func">COUNT</span>(*) * <span class="sql-num">100.0</span> / (<span class="sql-keyword">SELECT COUNT</span>(*) <span class="sql-keyword">FROM</span> netflix_titles), <span class="sql-num">2</span>) <span class="sql-keyword">AS</span> percentage<br>
    <span class="sql-keyword">FROM</span> netflix_titles<br>
    <span class="sql-keyword">WHERE</span> genre_primary <span class="sql-keyword">IS NOT NULL</span><br>
    <span class="sql-keyword">GROUP BY</span> genre_primary<br>
    <span class="sql-keyword">ORDER BY</span> title_count <span class="sql-keyword">DESC</span><br>
    <span class="sql-keyword">LIMIT</span> <span class="sql-num">10</span>;
  </div>

  <div class="sql-block no-break">
    <span class="sql-comment">-- Country Analysis: Top content-producing nations</span><br>
    <span class="sql-keyword">SELECT</span> country_primary,<br>
    &nbsp;&nbsp;&nbsp;&nbsp;<span class="sql-func">COUNT</span>(*) <span class="sql-keyword">AS</span> total,<br>
    &nbsp;&nbsp;&nbsp;&nbsp;<span class="sql-func">SUM</span>(<span class="sql-keyword">CASE WHEN</span> type=<span class="sql-string">'Movie'</span> <span class="sql-keyword">THEN</span> <span class="sql-num">1</span> <span class="sql-keyword">ELSE</span> <span class="sql-num">0</span> <span class="sql-keyword">END</span>) <span class="sql-keyword">AS</span> movies,<br>
    &nbsp;&nbsp;&nbsp;&nbsp;<span class="sql-func">SUM</span>(<span class="sql-keyword">CASE WHEN</span> type=<span class="sql-string">'TV Show'</span> <span class="sql-keyword">THEN</span> <span class="sql-num">1</span> <span class="sql-keyword">ELSE</span> <span class="sql-num">0</span> <span class="sql-keyword">END</span>) <span class="sql-keyword">AS</span> tv_shows<br>
    <span class="sql-keyword">FROM</span> netflix_titles<br>
    <span class="sql-keyword">WHERE</span> country_primary <span class="sql-keyword">IS NOT NULL</span><br>
    <span class="sql-keyword">GROUP BY</span> country_primary<br>
    <span class="sql-keyword">ORDER BY</span> total <span class="sql-keyword">DESC</span><br>
    <span class="sql-keyword">LIMIT</span> <span class="sql-num">15</span>;
  </div>
</div>

<div class="page-break"></div>

<!-- ============================= SECTION 7: METHODOLOGY & TECH ============================= -->
<div class="report-page">
  <div class="section-header">
    <div class="section-tag">Section 08</div>
    <div class="section-title">Methodology & Technology Stack</div>
    <div class="section-desc">Tools, techniques, and pipeline used in this analysis</div>
  </div>

  <div class="tech-grid no-break">
    <div class="tech-card">
      <div class="tech-icon">🗄️</div>
      <div class="tech-name">SQLite / SQL</div>
      <div class="tech-desc">Data storage, cleaning & analytical queries</div>
    </div>
    <div class="tech-card">
      <div class="tech-icon">🐍</div>
      <div class="tech-name">Python</div>
      <div class="tech-desc">Data ingestion, cleaning & transformation (pandas)</div>
    </div>
    <div class="tech-card">
      <div class="tech-icon">📊</div>
      <div class="tech-name">Excel</div>
      <div class="tech-desc">Pivot tables, charts & summary workbook</div>
    </div>
    <div class="tech-card">
      <div class="tech-icon">🌐</div>
      <div class="tech-name">JavaScript</div>
      <div class="tech-desc">Interactive Chart.js dashboard UI</div>
    </div>
  </div>

  <div class="insight-card" style="margin-bottom:20px;">
    <div class="insight-title">📐 Data Pipeline Architecture</div>
    <div class="insight-text">
      <strong>Step 1 — Ingestion:</strong> Raw Netflix dataset (8,807 rows × 12 columns) downloaded from public GitHub repository.<br><br>
      <strong>Step 2 — Cleaning:</strong> Python (pandas) script handled null values, fixed misplaced duration/rating fields, standardized date formats, extracted primary country/genre/director from multi-value fields.<br><br>
      <strong>Step 3 — Storage:</strong> Cleaned data loaded into SQLite database with proper schema, indexes, and normalized tables via SQL setup scripts.<br><br>
      <strong>Step 4 — Analysis:</strong> 5 layered SQL scripts executed — database setup → data cleaning → exploratory analysis → business insights → advanced analytics.<br><br>
      <strong>Step 5 — Visualization:</strong> Key aggregations exported to JSON and rendered in an interactive JavaScript dashboard using Chart.js with a cinematic dark UI.
    </div>
  </div>

  <div class="insight-grid no-break">
    <div class="insight-card">
      <div class="insight-title">📋 Dataset Facts</div>
      <div class="insight-text">
        • <strong>Source:</strong> Kaggle Netflix Movies & TV Shows<br>
        • <strong>Rows:</strong> 8,807 titles<br>
        • <strong>Columns:</strong> 12 fields<br>
        • <strong>Null Rate:</strong> ~15% across fields<br>
        • <strong>Period:</strong> {data['min_year']} – {data['max_year']}<br>
        • <strong>License:</strong> Public domain / CC0
      </div>
    </div>
    <div class="insight-card">
      <div class="insight-title">✅ Quality Assurance</div>
      <div class="insight-text">
        • Duplicate show_id detection and removal<br>
        • Misplaced rating ↔ duration field correction<br>
        • Date standardization to YYYY-MM-DD<br>
        • Multi-value field normalization<br>
        • NULL imputation with 'Unknown' labels<br>
        • Validated against original raw CSV
      </div>
    </div>
  </div>

  <hr class="pg-divider">

  <div class="section-header">
    <div class="section-tag">Section 09</div>
    <div class="section-title">Business Insights Summary</div>
    <div class="section-desc">Actionable takeaways from the analysis</div>
  </div>

  <div class="insight-grid no-break">
    <div class="insight-card highlight">
      <div class="insight-title">📈 Growth Peak</div>
      <div class="insight-text">
        Netflix's content additions peaked in 2019–2020, with significant acceleration
        from 2016 onward. This correlates with Netflix's global expansion into 190+
        countries in 2016 and aggressive original content spending.
      </div>
    </div>
    <div class="insight-card highlight">
      <div class="insight-title">🎬 Movie-Heavy Strategy</div>
      <div class="insight-text">
        Movies constitute ~{movies_pct}% of the catalog, but TV shows drive higher
        engagement per subscriber due to episodic consumption. Netflix has been
        increasing its TV show ratio year-over-year.
      </div>
    </div>
    <div class="insight-card highlight">
      <div class="insight-title">🌏 Global Localization</div>
      <div class="insight-text">
        Content from {data['countries']:,}+ countries signals deep localization.
        Indian, Korean, and European content has grown rapidly, with shows like
        Squid Game demonstrating massive global crossover potential.
      </div>
    </div>
    <div class="insight-card highlight">
      <div class="insight-title">⏱️ Optimal Movie Length</div>
      <div class="insight-text">
        Average movie duration of {data['avg_duration']} minutes aligns with
        cinema standards. Netflix's algorithm favors completion rates, making
        shorter films statistically more likely to receive promotion on the platform.
      </div>
    </div>
  </div>
</div>

<!-- ============================= FOOTER ============================= -->
<div class="report-footer">
  <div class="footer-logo">N</div>
  <p><strong>Netflix Content Analytics Report</strong></p>
  <p>Prepared by: Krish Verma &nbsp;·&nbsp; B.Tech Information Technology</p>
  <p>Dataset: Netflix Movies and TV Shows (8,807 titles) &nbsp;·&nbsp; September 2026</p>
  <p>Tools: SQL · Python · Excel · JavaScript · Chart.js</p>
  <p style="margin-top:16px; font-size:11px; color:#333;">
    This project is for educational and portfolio purposes. Netflix® is a registered trademark of Netflix, Inc.
  </p>
</div>

</body>
</html>
"""
    return html


if __name__ == '__main__':
    print("Fetching data from SQLite database...")
    data = fetch_data()
    print(f"  Total titles: {data['total']}")
    print(f"  Movies: {data['movies']}, TV Shows: {data['shows']}")
    print(f"  Countries: {data['countries']}")
    
    print("Generating HTML report...")
    html = generate_html_report(data)
    
    out_path = os.path.join(os.path.dirname(__file__), 'Netflix_Analytics_Report.html')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Report saved to: {out_path}")
    print("Open this file in Chrome and use Ctrl+P -> Save as PDF to generate the PDF!")
