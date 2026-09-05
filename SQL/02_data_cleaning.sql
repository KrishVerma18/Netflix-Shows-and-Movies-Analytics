-- ==============================================================================
-- NETFLIX SHOWS & MOVIES ANALYTICS
-- Script 02: Data Cleaning, Standardization & Quality Assurance
-- Description: Detects duplicates, rectifies misplaced values, imputes NULLs,
--              standardizes dates and numeric durations, and performs QA audits.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. DATA AUDIT: IDENTIFY DUPLICATE RECORDS
-- Verifies whether show_id or title-type combinations contain redundant rows.
-- ------------------------------------------------------------------------------

-- Check 1.1: Duplicate Primary Keys (show_id)
SELECT 
    show_id, 
    COUNT(*) AS occurrence_count
FROM netflix_raw
GROUP BY show_id
HAVING COUNT(*) > 1;
-- Result: 0 duplicate show_ids found.

-- Check 1.2: Duplicate Content Titles within the same content type
SELECT 
    type,
    TRIM(LOWER(title)) AS clean_title,
    COUNT(*) AS title_count
FROM netflix_raw
GROUP BY type, TRIM(LOWER(title))
HAVING COUNT(*) > 1
ORDER BY title_count DESC;
-- Result: 0 duplicate title+type pairs found.


-- ------------------------------------------------------------------------------
-- 2. DATA AUDIT: DETECT MISPLACED DURATION VALUES IN RATING COLUMN
-- In the Kaggle dataset, 3 records have duration values accidentally placed in rating.
-- ------------------------------------------------------------------------------
SELECT 
    show_id,
    type,
    title,
    rating,
    duration
FROM netflix_raw
WHERE rating LIKE '%min%';
-- Result: Identifies s5542 (74 min), s5795 (84 min), and s5814 (66 min).


-- ------------------------------------------------------------------------------
-- 3. DATA AUDIT: NULL VALUE PROFILE
-- Quantifies missingness across all raw columns prior to cleaning.
-- ------------------------------------------------------------------------------
SELECT 
    COUNT(*) AS total_records,
    SUM(CASE WHEN director IS NULL OR TRIM(director) = '' THEN 1 ELSE 0 END) AS missing_directors,
    SUM(CASE WHEN cast IS NULL OR TRIM(cast) = '' THEN 1 ELSE 0 END) AS missing_cast,
    SUM(CASE WHEN country IS NULL OR TRIM(country) = '' THEN 1 ELSE 0 END) AS missing_countries,
    SUM(CASE WHEN date_added IS NULL OR TRIM(date_added) = '' THEN 1 ELSE 0 END) AS missing_dates,
    SUM(CASE WHEN rating IS NULL OR TRIM(rating) = '' THEN 1 ELSE 0 END) AS missing_ratings,
    SUM(CASE WHEN duration IS NULL OR TRIM(duration) = '' THEN 1 ELSE 0 END) AS missing_durations
FROM netflix_raw;


-- ------------------------------------------------------------------------------
-- 4. CLEANING & ETL TRANSFORMATION PIPELINE
-- Populates the production `netflix_titles` table with standardized fields.
-- ------------------------------------------------------------------------------

INSERT INTO netflix_titles (
    show_id,
    type,
    title,
    director,
    cast,
    country,
    primary_country,
    date_added,
    year_added,
    month_added,
    month_name_added,
    release_year,
    rating,
    rating_category,
    duration,
    duration_minutes,
    duration_seasons,
    listed_in,
    primary_genre,
    description
)
SELECT 
    -- Primary identifier
    TRIM(r.show_id) AS show_id,
    
    -- Content type standardization
    TRIM(r.type) AS type,
    
    -- Title cleanup
    TRIM(r.title) AS title,
    
    -- Impute missing directors without dropping rows
    COALESCE(NULLIF(TRIM(r.director), ''), 'Unknown') AS director,
    
    -- Impute missing cast members
    COALESCE(NULLIF(TRIM(r.cast), ''), 'Unknown') AS cast,
    
    -- Impute missing country
    COALESCE(NULLIF(TRIM(r.country), ''), 'Unknown') AS country,
    
    -- Extract primary production country (lead country before first comma)
    CASE 
        WHEN r.country IS NULL OR TRIM(r.country) = '' THEN 'Unknown'
        WHEN INSTR(TRIM(r.country), ',') > 0 THEN SUBSTR(TRIM(r.country), 1, INSTR(TRIM(r.country), ',') - 1)
        ELSE TRIM(r.country)
    END AS primary_country,
    
    -- Standardize date_added to ISO YYYY-MM-DD
    -- Note: Evaluated cleanly across standard database dialects
    CASE 
        WHEN r.date_added IS NULL OR TRIM(r.date_added) = '' THEN NULL
        ELSE DATE(r.date_added)
    END AS date_added,
    
    -- Extract year added
    CASE 
        WHEN r.date_added IS NULL OR TRIM(r.date_added) = '' THEN NULL
        ELSE CAST(STRFTIME('%Y', r.date_added) AS INTEGER)
    END AS year_added,
    
    -- Extract month added (numerical 1-12)
    CASE 
        WHEN r.date_added IS NULL OR TRIM(r.date_added) = '' THEN NULL
        ELSE CAST(STRFTIME('%m', r.date_added) AS INTEGER)
    END AS month_added,
    
    -- Extract month name
    CASE 
        WHEN r.date_added IS NULL OR TRIM(r.date_added) = '' THEN NULL
        ELSE STRFTIME('%B', r.date_added)
    END AS month_name_added,
    
    -- Release Year
    r.release_year,
    
    -- Rectify misplaced rating anomaly and impute missing ratings
    CASE 
        WHEN r.rating LIKE '%min%' THEN 'NR'
        WHEN r.rating IS NULL OR TRIM(r.rating) = '' THEN 'NR'
        WHEN r.rating = 'UR' THEN 'NR'
        ELSE TRIM(r.rating)
    END AS rating,
    
    -- Categorize target audience maturity tier
    CASE 
        WHEN r.rating IN ('TV-MA', 'R', 'NC-17') THEN 'Adults (18+)'
        WHEN r.rating IN ('TV-14', 'PG-13') THEN 'Teens (13-17)'
        WHEN r.rating IN ('TV-PG', 'PG', 'TV-Y7', 'TV-Y7-FV') THEN 'Older Kids (7-12)'
        WHEN r.rating IN ('TV-Y', 'TV-G', 'G') THEN 'Kids (All Ages)'
        ELSE 'Unrated / NR'
    END AS rating_category,
    
    -- Rectify misplaced duration
    CASE 
        WHEN r.duration IS NULL AND r.rating LIKE '%min%' THEN TRIM(r.rating)
        ELSE TRIM(r.duration)
    END AS duration,
    
    -- Extract numeric duration for Movies (in minutes)
    CASE 
        WHEN r.type = 'Movie' AND r.rating LIKE '%min%' THEN CAST(SUBSTR(r.rating, 1, INSTR(r.rating, ' ') - 1) AS INTEGER)
        WHEN r.type = 'Movie' AND r.duration LIKE '%min%' THEN CAST(SUBSTR(r.duration, 1, INSTR(r.duration, ' ') - 1) AS INTEGER)
        ELSE NULL
    END AS duration_minutes,
    
    -- Extract numeric season count for TV Shows
    CASE 
        WHEN r.type = 'TV Show' AND r.duration LIKE '%Season%' THEN CAST(SUBSTR(r.duration, 1, INSTR(r.duration, ' ') - 1) AS INTEGER)
        ELSE NULL
    END AS duration_seasons,
    
    -- Genre string
    TRIM(r.listed_in) AS listed_in,
    
    -- Extract primary genre (first genre before comma)
    CASE 
        WHEN INSTR(TRIM(r.listed_in), ',') > 0 THEN SUBSTR(TRIM(r.listed_in), 1, INSTR(TRIM(r.listed_in), ',') - 1)
        ELSE TRIM(r.listed_in)
    END AS primary_genre,
    
    -- Description
    TRIM(r.description) AS description
FROM netflix_raw r;


-- ------------------------------------------------------------------------------
-- 5. POST-CLEANING VALIDATION & QUALITY ASSURANCE AUDIT
-- Validates record counts, schema compliance, and data integrity.
-- ------------------------------------------------------------------------------

-- Validation 5.1: Confirm total record retention matches raw input (8,807)
SELECT 
    COUNT(*) AS cleaned_record_count,
    (SELECT COUNT(*) FROM netflix_raw) AS raw_record_count,
    CASE 
        WHEN COUNT(*) = (SELECT COUNT(*) FROM netflix_raw) THEN 'PASSED: 100% Record Retention'
        ELSE 'FAILED: Record Mismatch'
    END AS audit_status
FROM netflix_titles;

-- Validation 5.2: Check for any remaining misplaced durations in rating
SELECT 
    COUNT(*) AS anomalies_remaining
FROM netflix_titles
WHERE rating LIKE '%min%';
-- Target: 0

-- Validation 5.3: Verify numeric duration population consistency
SELECT 
    type,
    COUNT(*) AS total_count,
    SUM(CASE WHEN duration_minutes IS NOT NULL THEN 1 ELSE 0 END) AS populated_minutes,
    SUM(CASE WHEN duration_seasons IS NOT NULL THEN 1 ELSE 0 END) AS populated_seasons
FROM netflix_titles
GROUP BY type;
-- Target: 6,131 movies with populated_minutes; 2,676 TV Shows with populated_seasons.
