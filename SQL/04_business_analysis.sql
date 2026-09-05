-- ==============================================================================
-- NETFLIX SHOWS & MOVIES ANALYTICS
-- Script 04: Core Business Analysis & Strategic Questions
-- Description: Solves 21 strategic business and content analytics questions
--              using rigorous analytical SQL. Adheres strictly to accurate
--              representation terminology ("highest represented", "most titles").
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- QUESTION 01: How many total titles are available in the Netflix catalog?
-- Business Context: Establishes the aggregate library volume across all formats.
-- ------------------------------------------------------------------------------
SELECT 
    COUNT(*) AS total_catalog_titles
FROM netflix_titles;


-- ------------------------------------------------------------------------------
-- QUESTION 02: What percentage of the catalog consists of Movies vs TV Shows?
-- Business Context: Analyzes Netflix's fundamental asset portfolio allocation.
-- ------------------------------------------------------------------------------
SELECT 
    type,
    COUNT(*) AS title_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM netflix_titles), 2) AS percentage_share
FROM netflix_titles
GROUP BY type
ORDER BY title_count DESC;


-- ------------------------------------------------------------------------------
-- QUESTION 03: How has Netflix content volume changed over the years?
-- Business Context: Measures year-over-year annual expansion trajectory.
-- ------------------------------------------------------------------------------
SELECT 
    year_added,
    COUNT(*) AS additions_in_year,
    SUM(CASE WHEN type = 'Movie' THEN 1 ELSE 0 END) AS movies_added,
    SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END) AS tv_shows_added
FROM netflix_titles
WHERE year_added IS NOT NULL
GROUP BY year_added
ORDER BY year_added ASC;


-- ------------------------------------------------------------------------------
-- QUESTION 04: Which years had the highest number of content additions?
-- Business Context: Identifies peak acquisition/release surges.
-- ------------------------------------------------------------------------------
SELECT 
    year_added,
    COUNT(*) AS total_additions
FROM netflix_titles
WHERE year_added IS NOT NULL
GROUP BY year_added
ORDER BY total_additions DESC
LIMIT 5;


-- ------------------------------------------------------------------------------
-- QUESTION 05: What are the most common genres across the entire platform?
-- Business Context: Examines catalog thematic distribution (de-duplicated).
-- ------------------------------------------------------------------------------
SELECT 
    g.genre,
    COUNT(DISTINCT g.show_id) AS total_titles_represented,
    ROUND(COUNT(DISTINCT g.show_id) * 100.0 / (SELECT COUNT(*) FROM netflix_titles), 2) AS catalog_penetration_pct
FROM netflix_genres g
GROUP BY g.genre
ORDER BY total_titles_represented DESC
LIMIT 15;


-- ------------------------------------------------------------------------------
-- QUESTION 06: Which genres are most represented for Movies?
-- Business Context: Highlights core focus areas in feature film licensing.
-- ------------------------------------------------------------------------------
SELECT 
    g.genre,
    COUNT(DISTINCT g.show_id) AS movie_titles_count
FROM netflix_genres g
JOIN netflix_titles t ON g.show_id = t.show_id
WHERE t.type = 'Movie'
GROUP BY g.genre
ORDER BY movie_titles_count DESC
LIMIT 10;


-- ------------------------------------------------------------------------------
-- QUESTION 07: Which genres are most represented for TV Shows?
-- Business Context: Identifies dominant episodic content genres.
-- ------------------------------------------------------------------------------
SELECT 
    g.genre,
    COUNT(DISTINCT g.show_id) AS tv_show_titles_count
FROM netflix_genres g
JOIN netflix_titles t ON g.show_id = t.show_id
WHERE t.type = 'TV Show'
GROUP BY g.genre
ORDER BY tv_show_titles_count DESC
LIMIT 10;


-- ------------------------------------------------------------------------------
-- QUESTION 08: Which countries produce the highest number of Netflix titles?
-- Business Context: Evaluates geographic production concentration (including co-productions).
-- ------------------------------------------------------------------------------
SELECT 
    c.country,
    COUNT(DISTINCT c.show_id) AS total_titles_produced,
    SUM(CASE WHEN t.type = 'Movie' THEN 1 ELSE 0 END) AS movies,
    SUM(CASE WHEN t.type = 'TV Show' THEN 1 ELSE 0 END) AS tv_shows
FROM netflix_countries c
JOIN netflix_titles t ON c.show_id = t.show_id
WHERE c.country <> 'Unknown'
GROUP BY c.country
ORDER BY total_titles_produced DESC
LIMIT 15;


-- ------------------------------------------------------------------------------
-- QUESTION 09: Which countries have the highest Movie-to-TV-Show production ratio?
-- Business Context: Detects market preferences between cinema and serialized television.
-- Filtering: Minimum 30 total titles to prevent single-title skewing.
-- ------------------------------------------------------------------------------
SELECT 
    c.country,
    SUM(CASE WHEN t.type = 'Movie' THEN 1 ELSE 0 END) AS movies,
    SUM(CASE WHEN t.type = 'TV Show' THEN 1 ELSE 0 END) AS tv_shows,
    COUNT(DISTINCT c.show_id) AS total_titles,
    ROUND(CAST(SUM(CASE WHEN t.type = 'Movie' THEN 1 ELSE 0 END) AS FLOAT) / 
          NULLIF(SUM(CASE WHEN t.type = 'TV Show' THEN 1 ELSE 0 END), 0), 2) AS movie_to_tv_ratio
FROM netflix_countries c
JOIN netflix_titles t ON c.show_id = t.show_id
WHERE c.country <> 'Unknown'
GROUP BY c.country
HAVING COUNT(DISTINCT c.show_id) >= 30
ORDER BY movie_to_tv_ratio DESC
LIMIT 10;


-- ------------------------------------------------------------------------------
-- QUESTION 10: What are the most common content ratings across the catalog?
-- Business Context: Determines target demographic and maturity profile.
-- ------------------------------------------------------------------------------
SELECT 
    rating,
    rating_category,
    COUNT(*) AS total_titles,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM netflix_titles), 2) AS pct_of_total
FROM netflix_titles
GROUP BY rating, rating_category
ORDER BY total_titles DESC;


-- ------------------------------------------------------------------------------
-- QUESTION 11: How do rating distributions differ between Movies and TV Shows?
-- Business Context: Compares maturity targeting between film and television assets.
-- ------------------------------------------------------------------------------
SELECT 
    rating,
    SUM(CASE WHEN type = 'Movie' THEN 1 ELSE 0 END) AS movies,
    ROUND(SUM(CASE WHEN type = 'Movie' THEN 1 ELSE 0 END) * 100.0 / (SELECT COUNT(*) FROM netflix_titles WHERE type = 'Movie'), 2) AS pct_of_all_movies,
    SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END) AS tv_shows,
    ROUND(SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END) * 100.0 / (SELECT COUNT(*) FROM netflix_titles WHERE type = 'TV Show'), 2) AS pct_of_all_tv_shows
FROM netflix_titles
GROUP BY rating
ORDER BY (movies + tv_shows) DESC;


-- ------------------------------------------------------------------------------
-- QUESTION 12: What is the average Movie duration across release decades?
-- Business Context: Assesses historical trends in film length and viewer expectations.
-- ------------------------------------------------------------------------------
SELECT 
    (release_year / 10) * 10 AS decade,
    COUNT(*) AS movies_count,
    ROUND(AVG(duration_minutes), 1) AS avg_duration_min,
    MIN(duration_minutes) AS min_duration_min,
    MAX(duration_minutes) AS max_duration_min
FROM netflix_titles
WHERE type = 'Movie' AND duration_minutes IS NOT NULL
GROUP BY (release_year / 10) * 10
ORDER BY decade ASC;


-- ------------------------------------------------------------------------------
-- QUESTION 13: What is the distribution of TV Shows by number of seasons?
-- Business Context: Measures franchise longevity and series renewal patterns.
-- ------------------------------------------------------------------------------
SELECT 
    CASE 
        WHEN duration_seasons = 1 THEN '1 Season (Limited / Initial)'
        WHEN duration_seasons = 2 THEN '2 Seasons'
        WHEN duration_seasons BETWEEN 3 AND 5 THEN '3 to 5 Seasons'
        ELSE '6+ Seasons (Long-Running Franchise)'
    END AS season_bracket,
    COUNT(*) AS tv_show_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM netflix_titles WHERE type = 'TV Show'), 2) AS pct_share
FROM netflix_titles
WHERE type = 'TV Show' AND duration_seasons IS NOT NULL
GROUP BY 
    CASE 
        WHEN duration_seasons = 1 THEN '1 Season (Limited / Initial)'
        WHEN duration_seasons = 2 THEN '2 Seasons'
        WHEN duration_seasons BETWEEN 3 AND 5 THEN '3 to 5 Seasons'
        ELSE '6+ Seasons (Long-Running Franchise)'
    END
ORDER BY tv_show_count DESC;


-- ------------------------------------------------------------------------------
-- QUESTION 14: Which directors have the highest number of titles on Netflix?
-- Business Context: Identifies prominent creative partners with largest volume.
-- ------------------------------------------------------------------------------
SELECT 
    d.director,
    COUNT(DISTINCT d.show_id) AS title_count,
    SUM(CASE WHEN t.type = 'Movie' THEN 1 ELSE 0 END) AS movie_count,
    SUM(CASE WHEN t.type = 'TV Show' THEN 1 ELSE 0 END) AS tv_show_count
FROM netflix_directors d
JOIN netflix_titles t ON d.show_id = t.show_id
WHERE d.director <> 'Unknown'
GROUP BY d.director
ORDER BY title_count DESC
LIMIT 10;


-- ------------------------------------------------------------------------------
-- QUESTION 15: Which actors appear most frequently across the Netflix catalog?
-- Business Context: Discovers talent recurring most frequently in acquisitions.
-- ------------------------------------------------------------------------------
SELECT 
    c.actor,
    COUNT(DISTINCT c.show_id) AS appearance_count,
    SUM(CASE WHEN t.type = 'Movie' THEN 1 ELSE 0 END) AS movies,
    SUM(CASE WHEN t.type = 'TV Show' THEN 1 ELSE 0 END) AS tv_shows
FROM netflix_cast c
JOIN netflix_titles t ON c.show_id = t.show_id
WHERE c.actor <> 'Unknown'
GROUP BY c.actor
ORDER BY appearance_count DESC
LIMIT 15;


-- ------------------------------------------------------------------------------
-- QUESTION 16: Which genres experienced the highest growth comparing recent periods?
-- Business Context: Compares additions between 2016-2018 and 2019-2021.
-- ------------------------------------------------------------------------------
WITH genre_periods AS (
    SELECT 
        g.genre,
        SUM(CASE WHEN t.year_added BETWEEN 2016 AND 2018 THEN 1 ELSE 0 END) AS additions_2016_2018,
        SUM(CASE WHEN t.year_added BETWEEN 2019 AND 2021 THEN 1 ELSE 0 END) AS additions_2019_2021
    FROM netflix_genres g
    JOIN netflix_titles t ON g.show_id = t.show_id
    GROUP BY g.genre
)
SELECT 
    genre,
    additions_2016_2018,
    additions_2019_2021,
    (additions_2019_2021 - additions_2016_2018) AS net_volume_growth,
    ROUND(((additions_2019_2021 - additions_2016_2018) * 100.0) / NULLIF(additions_2016_2018, 0), 2) AS pct_growth
FROM genre_periods
WHERE additions_2016_2018 >= 20
ORDER BY net_volume_growth DESC
LIMIT 10;


-- ------------------------------------------------------------------------------
-- QUESTION 17: Which countries show the strongest content additions in recent years?
-- Business Context: Tracks geographic expansion in global licensing investments.
-- ------------------------------------------------------------------------------
SELECT 
    c.country,
    SUM(CASE WHEN t.year_added = 2018 THEN 1 ELSE 0 END) AS additions_2018,
    SUM(CASE WHEN t.year_added = 2019 THEN 1 ELSE 0 END) AS additions_2019,
    SUM(CASE WHEN t.year_added = 2020 THEN 1 ELSE 0 END) AS additions_2020,
    SUM(CASE WHEN t.year_added = 2021 THEN 1 ELSE 0 END) AS additions_2021,
    COUNT(DISTINCT c.show_id) AS total_all_time
FROM netflix_countries c
JOIN netflix_titles t ON c.show_id = t.show_id
WHERE c.country <> 'Unknown'
GROUP BY c.country
HAVING COUNT(DISTINCT c.show_id) >= 50
ORDER BY additions_2020 DESC
LIMIT 10;


-- ------------------------------------------------------------------------------
-- QUESTION 18: What are the top 3 most represented genres within each major country?
-- Business Context: Uncovers regional genre profiles for major content hubs.
-- ------------------------------------------------------------------------------
WITH country_genre_counts AS (
    SELECT 
        c.country,
        g.genre,
        COUNT(DISTINCT c.show_id) AS titles_count,
        DENSE_RANK() OVER (PARTITION BY c.country ORDER BY COUNT(DISTINCT c.show_id) DESC) AS rank_in_country
    FROM netflix_countries c
    JOIN netflix_genres g ON c.show_id = g.show_id
    WHERE c.country IN ('United States', 'India', 'United Kingdom', 'Japan', 'South Korea', 'Canada')
    GROUP BY c.country, g.genre
)
SELECT 
    country,
    rank_in_country,
    genre,
    titles_count
FROM country_genre_counts
WHERE rank_in_country <= 3
ORDER BY country, rank_in_country;


-- ------------------------------------------------------------------------------
-- QUESTION 19: Rank countries by total title volume using window functions.
-- Business Context: Establishes global content leaderboard without collapsing ties.
-- ------------------------------------------------------------------------------
SELECT 
    country,
    COUNT(DISTINCT show_id) AS title_volume,
    RANK() OVER (ORDER BY COUNT(DISTINCT show_id) DESC) AS global_rank,
    DENSE_RANK() OVER (ORDER BY COUNT(DISTINCT show_id) DESC) AS global_dense_rank
FROM netflix_countries
WHERE country <> 'Unknown'
GROUP BY country
ORDER BY global_rank ASC
LIMIT 15;


-- ------------------------------------------------------------------------------
-- QUESTION 20: What is the average time lag (years) from theatrical release to Netflix?
-- Business Context: Determines whether Netflix functions primarily as a premiering platform
--                   or an archival / secondary syndication distributor across years.
-- ------------------------------------------------------------------------------
SELECT 
    year_added,
    COUNT(*) AS titles_added,
    ROUND(AVG(year_added - release_year), 2) AS avg_release_to_addition_lag_years,
    ROUND(AVG(CASE WHEN type = 'Movie' THEN year_added - release_year END), 2) AS avg_movie_lag_years,
    ROUND(AVG(CASE WHEN type = 'TV Show' THEN year_added - release_year END), 2) AS avg_tv_show_lag_years
FROM netflix_titles
WHERE year_added IS NOT NULL AND year_added >= release_year
GROUP BY year_added
ORDER BY year_added ASC;


-- ------------------------------------------------------------------------------
-- QUESTION 21: Identify high-volume multi-dimensional content segments.
-- Business Context: Pinpoints the catalog's densest intersections of Country + Type + Rating.
-- ------------------------------------------------------------------------------
SELECT 
    primary_country,
    type,
    rating,
    COUNT(*) AS titles_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM netflix_titles), 2) AS catalog_pct
FROM netflix_titles
WHERE primary_country <> 'Unknown'
GROUP BY primary_country, type, rating
HAVING COUNT(*) >= 50
ORDER BY titles_count DESC
LIMIT 10;
