import pandas as pd
import numpy as np
import re
import os

def clean_netflix_data():
    raw_path = os.path.join('Dataset', 'netflix_titles_raw.csv')
    cleaned_path = os.path.join('Dataset', 'netflix_titles_cleaned.csv')

    df = pd.read_csv(raw_path)
    print(f"Loaded raw dataset with shape: {df.shape}")

    # 1. Strip whitespace on string columns
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({'nan': np.nan, 'None': np.nan, '': np.nan})

    # 2. Fix the 3 misplaced ratings where duration is in rating column
    misplaced_mask = df['rating'].str.contains('min', na=False)
    print(f"Found {misplaced_mask.sum()} misplaced duration rows in rating column.")
    for idx in df[misplaced_mask].index:
        df.loc[idx, 'duration'] = df.loc[idx, 'rating']
        df.loc[idx, 'rating'] = 'NR'

    # 3. Handle missing ratings
    df['rating'] = df['rating'].fillna('NR')
    df['rating'] = df['rating'].replace({'UR': 'NR'})

    # 4. Handle missing text fields without deleting rows
    df['director'] = df['director'].fillna('Unknown')
    df['cast'] = df['cast'].fillna('Unknown')
    df['country'] = df['country'].fillna('Unknown')

    # 5. Extract primary country
    df['primary_country'] = df['country'].apply(lambda x: x.split(',')[0].strip() if pd.notnull(x) and x != 'Unknown' else 'Unknown')

    # 6. Parse date_added
    date_clean = pd.to_datetime(df['date_added'].str.strip(), errors='coerce')
    df['date_added'] = date_clean.dt.strftime('%Y-%m-%d')
    df['year_added'] = date_clean.dt.year.astype('Int64')
    df['month_added'] = date_clean.dt.month.astype('Int64')
    df['month_name_added'] = date_clean.dt.strftime('%B')

    # 7. Extract numeric duration
    def parse_duration_min(row):
        if row['type'] == 'Movie' and pd.notnull(row['duration']):
            m = re.search(r'(\d+)\s*min', str(row['duration']))
            if m:
                return int(m.group(1))
        return np.nan

    def parse_duration_seasons(row):
        if row['type'] == 'TV Show' and pd.notnull(row['duration']):
            m = re.search(r'(\d+)\s*Season', str(row['duration']))
            if m:
                return int(m.group(1))
        return np.nan

    df['duration_minutes'] = df.apply(parse_duration_min, axis=1).astype('Int64')
    df['duration_seasons'] = df.apply(parse_duration_seasons, axis=1).astype('Int64')

    # 8. Primary genre
    df['primary_genre'] = df['listed_in'].apply(lambda x: x.split(',')[0].strip())

    # 9. Target audience / rating category
    def map_rating_category(r):
        if r in ['TV-MA', 'R', 'NC-17']:
            return 'Adults (18+)'
        elif r in ['TV-14', 'PG-13']:
            return 'Teens (13-17)'
        elif r in ['TV-PG', 'PG', 'TV-Y7', 'TV-Y7-FV']:
            return 'Older Kids (7-12)'
        elif r in ['TV-Y', 'TV-G', 'G']:
            return 'Kids (All Ages)'
        else:
            return 'Unrated / NR'

    df['rating_category'] = df['rating'].apply(map_rating_category)

    print(f"Cleaned dataset shape: {df.shape}")
    print("Null count check after cleaning:")
    print(df.isnull().sum())

    # Reorder columns logically
    cols = [
        'show_id', 'type', 'title', 'director', 'cast', 'country', 'primary_country',
        'date_added', 'year_added', 'month_added', 'month_name_added', 'release_year',
        'rating', 'rating_category', 'duration', 'duration_minutes', 'duration_seasons',
        'listed_in', 'primary_genre', 'description'
    ]
    df_out = df[cols]
    df_out.to_csv(cleaned_path, index=False)
    print(f"Successfully exported cleaned data to: {cleaned_path}")

    # Generate normalized relational tables for SQL verification & loading
    # Directors normalized
    dir_rows = []
    for _, row in df.iterrows():
        sid = row['show_id']
        dirs = [d.strip() for d in str(row['director']).split(',') if d.strip() and d.strip() != 'Unknown']
        for d in dirs:
            dir_rows.append({'show_id': sid, 'director': d})
    df_dirs = pd.DataFrame(dir_rows)
    df_dirs.to_csv(os.path.join('Dataset', 'relational_directors.csv'), index=False)

    # Cast normalized
    cast_rows = []
    for _, row in df.iterrows():
        sid = row['show_id']
        casts = [c.strip() for c in str(row['cast']).split(',') if c.strip() and c.strip() != 'Unknown']
        for c in casts:
            cast_rows.append({'show_id': sid, 'actor': c})
    df_cast = pd.DataFrame(cast_rows)
    df_cast.to_csv(os.path.join('Dataset', 'relational_cast.csv'), index=False)

    # Countries normalized
    country_rows = []
    for _, row in df.iterrows():
        sid = row['show_id']
        cntrs = [c.strip() for c in str(row['country']).split(',') if c.strip() and c.strip() != 'Unknown']
        for c in cntrs:
            country_rows.append({'show_id': sid, 'country': c})
    df_country = pd.DataFrame(country_rows)
    df_country.to_csv(os.path.join('Dataset', 'relational_countries.csv'), index=False)

    # Genres normalized
    genre_rows = []
    for _, row in df.iterrows():
        sid = row['show_id']
        gnrs = [g.strip() for g in str(row['listed_in']).split(',') if g.strip()]
        for g in gnrs:
            genre_rows.append({'show_id': sid, 'genre': g})
    df_genre = pd.DataFrame(genre_rows)
    df_genre.to_csv(os.path.join('Dataset', 'relational_genres.csv'), index=False)

    print("Generated normalized relational mapping CSVs for SQL relational modeling.")

if __name__ == '__main__':
    clean_netflix_data()
