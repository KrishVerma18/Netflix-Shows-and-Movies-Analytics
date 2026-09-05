-- ==============================================================================
-- NETFLIX SHOWS & MOVIES ANALYTICS
-- Script 05: Advanced Analytical SQL & Portfolio Showcase
-- Description: Implements CTEs, subqueries, complex window functions,
--              cumulative running totals, Year-over-Year (YoY) growth,
--              rolling moving averages, and multi-dimensional segmentations.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. CUMULATIVE CATALOG GROWTH & YEAR-OVER-YEAR (YoY) GROWTH RATE
-- Technique: Multi-level CTE + Window SUM() + Window LAG()
-- Business Application: Evaluates platform scaling velocity and annual momentum.
-- ------------------------------------------------------------------------------
WITH annual_additions AS (
    SELECT 
        year_added,
        COUNT(*) AS additions_count,
        SUM(CASE WHEN type = 'Movie' THEN 1 ELSE 0 END) AS movies_added,
        SUM(CASE WHEN type = 'TV Show' THEN 1 ELSE 0 END) AS tv_shows_added
    FROM netflix_titles
    WHERE year_added IS NOT NULL
    GROUP BY year_added
),
catalog_metrics AS (
    SELECT 
        year_added,
        additions_count,
        movies_added,
        tv_shows_added,
        -- Cumulative running total of all titles
        SUM(additions_count) OVER (
            ORDER BY year_added 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_catalog_size,
        -- Previous year's additions using LAG
        LAG(additions_count, 1) OVER (
            ORDER BY year_added
        ) AS prev_year_additions
    FROM annual_additions
)
SELECT 
    year_added,
    additions_count,
    movies_added,
    tv_shows_added,
    cumulative_catalog_size,
    COALESCE(prev_year_additions, 0) AS prev_year_additions,
    -- Calculate Year-over-Year (YoY) growth percentage
    ROUND(
        ((additions_count - prev_year_additions) * 100.0) / NULLIF(prev_year_additions, 0), 
        2
    ) AS yoy_growth_pct
FROM catalog_metrics
ORDER BY year_added ASC;


-- ------------------------------------------------------------------------------
-- 2. ROLLING 3-YEAR MOVING AVERAGE OF CONTENT ADDITIONS
-- Technique: Window AVG() with sliding frame (ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)
-- Business Application: Smooths out annual licensing spikes to discern underlying trend.
-- ------------------------------------------------------------------------------
WITH yearly_counts AS (
    SELECT 
        year_added,
        COUNT(*) AS annual_volume
    FROM netflix_titles
    WHERE year_added IS NOT NULL
    GROUP BY year_added
)
SELECT 
    year_added,
    annual_volume,
    ROUND(
        AVG(annual_volume) OVER (
            ORDER BY year_added 
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ), 
        1
    ) AS rolling_3yr_avg_volume,
    MIN(annual_volume) OVER (
        ORDER BY year_added 
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS rolling_3yr_min,
    MAX(annual_volume) OVER (
        ORDER BY year_added 
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS rolling_3yr_max
FROM yearly_counts
ORDER BY year_added ASC;


-- ------------------------------------------------------------------------------
-- 3. DENSE_RANKING TOP 3 DIRECTORS PER TOP PRODUCING COUNTRY
-- Technique: CTE + DENSE_RANK() + PARTITION BY
-- Business Application: Highlights dominant localized creative partnerships.
-- ------------------------------------------------------------------------------
WITH top_countries AS (
    SELECT country
    FROM netflix_countries
    WHERE country <> 'Unknown'
    GROUP BY country
    ORDER BY COUNT(DISTINCT show_id) DESC
    LIMIT 5
),
director_rankings AS (
    SELECT 
        c.country,
        d.director,
        COUNT(DISTINCT d.show_id) AS titles_directed,
        DENSE_RANK() OVER (
            PARTITION BY c.country 
            ORDER BY COUNT(DISTINCT d.show_id) DESC
        ) AS rank_in_country
    FROM netflix_directors d
    JOIN netflix_countries c ON d.show_id = c.show_id
    WHERE c.country IN (SELECT country FROM top_countries)
      AND d.director <> 'Unknown'
    GROUP BY c.country, d.director
)
SELECT 
    country,
    rank_in_country,
    director,
    titles_directed
FROM director_rankings
WHERE rank_in_country <= 3
ORDER BY country, rank_in_country, titles_directed DESC;


-- ------------------------------------------------------------------------------
-- 4. RUNTIME QUARTILE DISTRIBUTION & OUTLIER DETECTION FOR MOVIES
-- Technique: NTILE(4) Window Function + CASE Expressions
-- Business Application: Segments movies into runtime quartiles for scheduling.
-- ------------------------------------------------------------------------------
WITH movie_quartiles AS (
    SELECT 
        show_id,
        title,
        release_year,
        duration_minutes,
        NTILE(4) OVER (ORDER BY duration_minutes ASC) AS runtime_quartile
    FROM netflix_titles
    WHERE type = 'Movie' AND duration_minutes IS NOT NULL
)
SELECT 
    runtime_quartile,
    CASE runtime_quartile
        WHEN 1 THEN 'Q1: Short Feature (< 25th percentile)'
        WHEN 2 THEN 'Q2: Standard Lower (25th - 50th percentile)'
        WHEN 3 THEN 'Q3: Standard Upper (50th - 75th percentile)'
        WHEN 4 THEN 'Q4: Extended / Epic (> 75th percentile)'
    END AS quartile_label,
    COUNT(*) AS movie_count,
    MIN(duration_minutes) AS min_runtime_min,
    MAX(duration_minutes) AS max_runtime_min,
    ROUND(AVG(duration_minutes), 1) AS avg_runtime_min
FROM movie_quartiles
GROUP BY runtime_quartile
ORDER BY runtime_quartile ASC;


-- ------------------------------------------------------------------------------
-- 5. CONTENT FRESHNESS INDEX: SAME-YEAR RELEASES VS ARCHIVAL LICENSING
-- Technique: CASE aggregation + Percentage Calculation by Addition Year
-- Business Application: Evaluates Netflix's pivot from legacy library licensing
--                       to day-and-date / contemporary premiering platform.
-- ------------------------------------------------------------------------------
SELECT 
    year_added,
    COUNT(*) AS total_additions,
    -- Fresh content: Added within 0-1 years of original theatrical release
    SUM(CASE WHEN (year_added - release_year) <= 1 THEN 1 ELSE 0 END) AS fresh_titles_count,
    -- Archival content: Released 5+ years prior to platform addition
    SUM(CASE WHEN (year_added - release_year) >= 5 THEN 1 ELSE 0 END) AS archival_titles_count,
    ROUND(
        SUM(CASE WHEN (year_added - release_year) <= 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 
        2
    ) AS fresh_content_share_pct,
    ROUND(
        SUM(CASE WHEN (year_added - release_year) >= 5 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 
        2
    ) AS archival_content_share_pct
FROM netflix_titles
WHERE year_added IS NOT NULL AND year_added >= release_year
GROUP BY year_added
HAVING COUNT(*) >= 50
ORDER BY year_added ASC;


-- ------------------------------------------------------------------------------
-- 6. CO-PRODUCTION NETWORK ANALYSIS: DOMESTIC VS INTERNATIONAL COLLABORATIONS
-- Technique: String parsing condition + Group aggregations
-- Business Application: Quantifies how frequently content spans multiple nations.
-- ------------------------------------------------------------------------------
SELECT 
    type,
    CASE 
        WHEN country = 'Unknown' THEN 'Country Not Specified'
        WHEN INSTR(country, ',') > 0 THEN 'Multi-Country Co-Production'
        ELSE 'Single-Country Production'
    END AS production_scope,
    COUNT(*) AS title_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM netflix_titles), 2) AS catalog_pct
FROM netflix_titles
GROUP BY 
    type,
    CASE 
        WHEN country = 'Unknown' THEN 'Country Not Specified'
        WHEN INSTR(country, ',') > 0 THEN 'Multi-Country Co-Production'
        ELSE 'Single-Country Production'
    END
ORDER BY type, title_count DESC;


-- ------------------------------------------------------------------------------
-- 7. TOP DIRECTOR-ACTOR CREATIVE COLLABORATION PAIRS
-- Technique: Relational JOINs across normalized entities + Self-exclusion
-- Business Application: Identifies recurring high-volume director-actor duos.
-- ------------------------------------------------------------------------------
SELECT 
    d.director,
    c.actor,
    COUNT(DISTINCT d.show_id) AS collaborative_titles
FROM netflix_directors d
JOIN netflix_cast c ON d.show_id = c.show_id
JOIN netflix_titles t ON d.show_id = t.show_id
WHERE d.director <> 'Unknown' 
  AND c.actor <> 'Unknown'
  AND d.director <> c.actor -- Exclude self-directed performances
GROUP BY d.director, c.actor
HAVING COUNT(DISTINCT d.show_id) >= 3
ORDER BY collaborative_titles DESC
LIMIT 10;
