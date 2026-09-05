import sqlite3
import pandas as pd
import os

def test_sql():
    db_path = 'netflix_analytics.db'
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    print("Created SQLite database connection.")

    # 1. Run 01_database_setup.sql
    with open('SQL/01_database_setup.sql', 'r', encoding='utf-8') as f:
        setup_sql = f.read()
    # Filter out multi-line comments and split statements
    cur.executescript(setup_sql)
    print("Executed 01_database_setup.sql successfully.")

    # 2. Populate netflix_raw from raw CSV
    df_raw = pd.read_csv('Dataset/netflix_titles_raw.csv')
    df_raw.to_sql('netflix_raw', conn, if_exists='append', index=False)
    print(f"Loaded {len(df_raw)} records into netflix_raw.")

    # 3. Populate netflix_titles from cleaned CSV
    df_clean = pd.read_csv('Dataset/netflix_titles_cleaned.csv')
    df_clean.to_sql('netflix_titles', conn, if_exists='append', index=False)
    print(f"Loaded {len(df_clean)} records into netflix_titles.")

    # 4. Populate normalized relational tables
    df_dirs = pd.read_csv('Dataset/relational_directors.csv')
    df_dirs['director_id'] = range(1, len(df_dirs) + 1)
    df_dirs[['director_id', 'show_id', 'director']].to_sql('netflix_directors', conn, if_exists='append', index=False)

    df_cast = pd.read_csv('Dataset/relational_cast.csv')
    df_cast['cast_id'] = range(1, len(df_cast) + 1)
    df_cast[['cast_id', 'show_id', 'actor']].to_sql('netflix_cast', conn, if_exists='append', index=False)

    df_cntry = pd.read_csv('Dataset/relational_countries.csv')
    df_cntry['country_id'] = range(1, len(df_cntry) + 1)
    df_cntry[['country_id', 'show_id', 'country']].to_sql('netflix_countries', conn, if_exists='append', index=False)

    df_gnr = pd.read_csv('Dataset/relational_genres.csv')
    df_gnr['genre_id'] = range(1, len(df_gnr) + 1)
    df_gnr[['genre_id', 'show_id', 'genre']].to_sql('netflix_genres', conn, if_exists='append', index=False)
    print("Loaded all normalized relational tables.")

    # Test running queries from 03, 04, 05
    scripts = [
        'SQL/03_exploratory_analysis.sql',
        'SQL/04_business_analysis.sql',
        'SQL/05_advanced_analysis.sql'
    ]

    for script_file in scripts:
        print(f"\n--- Testing queries in {script_file} ---")
        with open(script_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split into separate queries by semicolon
        # Clean comment blocks
        queries = [q.strip() for q in content.split(';') if q.strip()]
        valid_queries = 0
        for i, q in enumerate(queries):
            # Check if it has SELECT
            if 'SELECT' in q.upper():
                try:
                    res = pd.read_sql_query(q, conn)
                    valid_queries += 1
                except Exception as e:
                    print(f"Error in query {i+1} in {script_file}:\n{q[:150]}...\nError: {e}")
                    raise e
        print(f"All {valid_queries} analytical queries in {script_file} executed successfully!")

    conn.close()
    print("\nAll SQL scripts tested and verified against actual database!")

if __name__ == '__main__':
    test_sql()
