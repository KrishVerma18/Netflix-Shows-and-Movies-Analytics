-- ==============================================================================
-- NETFLIX SHOWS & MOVIES ANALYTICS
-- Script 03: Exploratory Data Analysis (EDA)
-- Description: Establishes baseline descriptive statistics, catalog volume,
--              type distributions, ratings breakdown, and temporal patterns.
-- SQL Concepts: SELECT, WHERE, ORDER BY, DISTINCT, COUNT, SUM, AVG, MIN, MAX,
--               GROUP BY, HAVING, CASE, ROUND.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. CATALOG OVERVIEW & TOTAL RECORD VOLUME
-- Baseline metric establishing total distinct assets in the Netflix catalog.
-- ------------------------------------------------------------------------------
SELECT 
    COUNT(*) AS total_titles,
    COUNT(DISTINCT title) AS distinct_titles,
    MIN(release_year) AS earliest_release_year,
    MAX(release_year) AS latest_release_year,
    MIN(date_added) AS earliest_date_added,
    MAX(date_added) AS latest_date_added
FROM netflix_titles;


-- ------------------------------------------------------------------------------
-- 2. CONTENT TYPE COMPOSITION: MOVIES VS TV SHOWS
-- Compares catalog volume and percentage share between Movies and TV Shows.
-- ------------------------------------------------------------------------------
SELECT 
    type,
    COUNT(*) AS total_content,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM netflix_titles), 2) AS percentage_of_catalog
FROM netflix_titles
GROUP BY type
ORDER BY total_content DESC;


-- ------------------------------------------------------------------------------
-- 3. DIVERSITY & CARDINALITY AUDIT
-- Analyzes unique counts across creators, talent, regions, and genres.
-- ------------------------------------------------------------------------------
SELECT 
    COUNT(DISTINCT director) AS unique_directors_raw,
    COUNT(DISTINCT primary_country) AS unique_primary_countries,
    COUNT(DISTINCT rating) AS unique_ratings,
    COUNT(DISTINCT primary_genre) AS unique_primary_genres
FROM netflix_titles;


-- ------------------------------------------------------------------------------
-- 4. CONTENT MATURITY & RATINGS DISTRIBUTION
-- Categorizes titles by content rating certifications and target demographic.
-- ------------------------------------------------------------------------------
SELECT 
    rating,
    rating_category,
    COUNT(*) AS title_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM netflix_titles), 2) AS pct_share
FROM netflix_titles
GROUP BY rating, rating_category
ORDER BY title_count DESC;


-- ------------------------------------------------------------------------------
-- 5. RATINGS DISTRIBUTION SPLIT BY CONTENT TYPE
-- Analyzes how age classifications diverge between feature films and series.
-- ------------------------------------------------------------------------------
SELECT 
    rating,
    SUM(CASE WHEN type = 'Movie' THEN 1 ELSE 0 END) AS movie_count,
    SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END) AS tv_show_count,
    COUNT(*) AS total_count
FROM netflix_titles
GROUP BY rating
ORDER BY total_count DESC;


-- ------------------------------------------------------------------------------
-- 6. CONTENT RELEASE DECADES ANALYSIS
-- Evaluates the distribution of content based on original release decade.
-- ------------------------------------------------------------------------------
SELECT 
    (release_year / 10) * 10 AS release_decade,
    COUNT(*) AS total_titles,
    SUM(CASE WHEN type = 'Movie' THEN 1 ELSE 0 END) AS movies,
    SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END) AS tv_shows
FROM netflix_titles
GROUP BY (release_year / 10) * 10
ORDER BY release_decade DESC;


-- ------------------------------------------------------------------------------
-- 7. NETFLIX ADDITIONS BY CALENDAR YEAR
-- Tracks the expansion pace of the catalog from 2008 to 2021.
-- ------------------------------------------------------------------------------
SELECT 
    year_added,
    COUNT(*) AS titles_added,
    SUM(CASE WHEN type = 'Movie' THEN 1 ELSE 0 END) AS movies_added,
    SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END) AS tv_shows_added
FROM netflix_titles
WHERE year_added IS NOT NULL
GROUP BY year_added
ORDER BY year_added ASC;


-- ------------------------------------------------------------------------------
-- 8. SEASONALITY OF CONTENT ADDITIONS (MONTHLY DISTRIBUTION)
-- Evaluates which calendar months observe peak content ingestion.
-- ------------------------------------------------------------------------------
SELECT 
    month_added,
    month_name_added,
    COUNT(*) AS total_additions,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM netflix_titles WHERE month_added IS NOT NULL), 2) AS monthly_share_pct
FROM netflix_titles
WHERE month_added IS NOT NULL
GROUP BY month_added, month_name_added
ORDER BY month_added ASC;


-- ------------------------------------------------------------------------------
-- 9. MOVIE DURATION BENCHMARKS & RUNTIME SPREAD
-- Computes key descriptive metrics for feature film running times (minutes).
-- ------------------------------------------------------------------------------
SELECT 
    MIN(duration_minutes) AS shortest_movie_minutes,
    MAX(duration_minutes) AS longest_movie_minutes,
    ROUND(AVG(duration_minutes), 2) AS average_movie_duration,
    COUNT(*) AS total_movies_evaluated
FROM netflix_titles
WHERE type = 'Movie' AND duration_minutes IS NOT NULL;


-- ------------------------------------------------------------------------------
-- 10. TV SHOW SEASON DISTRIBUTION & LONGEVITY
-- Details the proportion of television shows by total seasons produced.
-- ------------------------------------------------------------------------------
SELECT 
    duration_seasons AS seasons,
    COUNT(*) AS show_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM netflix_titles WHERE type = 'TV Show'), 2) AS pct_of_tv_shows
FROM netflix_titles
WHERE type = 'TV Show' AND duration_seasons IS NOT NULL
GROUP BY duration_seasons
ORDER BY seasons ASC;


-- ------------------------------------------------------------------------------
-- 11. SHORTEST & LONGEST TITLES ON NETFLIX
-- Identifies extreme duration outliers in movies and TV shows.
-- ------------------------------------------------------------------------------

-- Top 5 Shortest Movies
SELECT title, release_year, duration_minutes, country
FROM netflix_titles
WHERE type = 'Movie' AND duration_minutes IS NOT NULL
ORDER BY duration_minutes ASC
LIMIT 5;

-- Top 5 Longest Movies
SELECT title, release_year, duration_minutes, country
FROM netflix_titles
WHERE type = 'Movie' AND duration_minutes IS NOT NULL
ORDER BY duration_minutes DESC
LIMIT 5;

-- Top 5 Longest-Running TV Shows by Season Count
SELECT title, release_year, duration_seasons, country
FROM netflix_titles
WHERE type = 'TV Show' AND duration_seasons IS NOT NULL
ORDER BY duration_seasons DESC
LIMIT 5;
