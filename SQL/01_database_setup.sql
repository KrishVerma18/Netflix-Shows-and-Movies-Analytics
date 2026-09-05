-- ==============================================================================
-- NETFLIX SHOWS & MOVIES ANALYTICS
-- Script 01: Database Setup & Schema Architecture
-- Description: Creates the staging table, production cleaned table, and 
--              normalized relational tables (directors, cast, countries, genres)
--              with primary keys, foreign keys, and analytical indexes.
-- Target Engines: PostgreSQL, MySQL 8+, SQLite 3
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. DROP EXISTING TABLES (Idempotent execution)
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS netflix_genres;
DROP TABLE IF EXISTS netflix_countries;
DROP TABLE IF EXISTS netflix_cast;
DROP TABLE IF EXISTS netflix_directors;
DROP TABLE IF EXISTS netflix_titles;
DROP TABLE IF EXISTS netflix_raw;

-- ------------------------------------------------------------------------------
-- 2. STAGING TABLE: netflix_raw
-- Stores the pristine, unmodified dataset exactly as ingested from CSV.
-- ------------------------------------------------------------------------------
CREATE TABLE netflix_raw (
    show_id         VARCHAR(10) PRIMARY KEY,
    type            VARCHAR(10),
    title           VARCHAR(255),
    director        TEXT,
    cast            TEXT,
    country         VARCHAR(255),
    date_added      VARCHAR(50),
    release_year    INTEGER,
    rating          VARCHAR(20),
    duration        VARCHAR(50),
    listed_in       VARCHAR(255),
    description     TEXT
);

-- ------------------------------------------------------------------------------
-- 3. PRODUCTION TABLE: netflix_titles
-- Cleaned, standardized, and enriched production entity table.
-- ------------------------------------------------------------------------------
CREATE TABLE netflix_titles (
    show_id             VARCHAR(10) PRIMARY KEY,
    type                VARCHAR(10) NOT NULL,
    title               VARCHAR(255) NOT NULL,
    director            TEXT,
    cast                TEXT,
    country             VARCHAR(255),
    primary_country     VARCHAR(100),
    date_added          DATE,
    year_added          INTEGER,
    month_added         INTEGER,
    month_name_added    VARCHAR(20),
    release_year        INTEGER NOT NULL,
    rating              VARCHAR(20) NOT NULL,
    rating_category     VARCHAR(50) NOT NULL,
    duration            VARCHAR(50),
    duration_minutes    INTEGER,
    duration_seasons    INTEGER,
    listed_in           VARCHAR(255),
    primary_genre       VARCHAR(100),
    description         TEXT
);

-- ------------------------------------------------------------------------------
-- 4. NORMALIZED RELATIONAL TABLES
-- Resolves 1-to-many relationships for deep granular analytics.
-- ------------------------------------------------------------------------------

-- Table: netflix_directors (Resolves multi-director titles)
CREATE TABLE netflix_directors (
    director_id     INTEGER PRIMARY KEY,
    show_id         VARCHAR(10) NOT NULL,
    director        VARCHAR(150) NOT NULL,
    FOREIGN KEY (show_id) REFERENCES netflix_titles(show_id) ON DELETE CASCADE
);

-- Table: netflix_cast (Resolves multi-actor appearances)
CREATE TABLE netflix_cast (
    cast_id         INTEGER PRIMARY KEY,
    show_id         VARCHAR(10) NOT NULL,
    actor           VARCHAR(150) NOT NULL,
    FOREIGN KEY (show_id) REFERENCES netflix_titles(show_id) ON DELETE CASCADE
);

-- Table: netflix_countries (Resolves multi-country international co-productions)
CREATE TABLE netflix_countries (
    country_id      INTEGER PRIMARY KEY,
    show_id         VARCHAR(10) NOT NULL,
    country         VARCHAR(100) NOT NULL,
    FOREIGN KEY (show_id) REFERENCES netflix_titles(show_id) ON DELETE CASCADE
);

-- Table: netflix_genres (Resolves multiple genre categorizations per title)
CREATE TABLE netflix_genres (
    genre_id        INTEGER PRIMARY KEY,
    show_id         VARCHAR(10) NOT NULL,
    genre           VARCHAR(100) NOT NULL,
    FOREIGN KEY (show_id) REFERENCES netflix_titles(show_id) ON DELETE CASCADE
);

-- ------------------------------------------------------------------------------
-- 5. PERFORMANCE & ANALYTICAL INDEXES
-- Optimizes filtering, grouping, and join operations on frequent analytical paths.
-- ------------------------------------------------------------------------------
CREATE INDEX idx_titles_type ON netflix_titles(type);
CREATE INDEX idx_titles_release_year ON netflix_titles(release_year);
CREATE INDEX idx_titles_year_added ON netflix_titles(year_added);
CREATE INDEX idx_titles_rating ON netflix_titles(rating);
CREATE INDEX idx_titles_primary_country ON netflix_titles(primary_country);
CREATE INDEX idx_titles_primary_genre ON netflix_titles(primary_genre);

CREATE INDEX idx_directors_name ON netflix_directors(director);
CREATE INDEX idx_cast_actor ON netflix_cast(actor);
CREATE INDEX idx_countries_country ON netflix_countries(country);
CREATE INDEX idx_genres_genre ON netflix_genres(genre);

-- ------------------------------------------------------------------------------
-- 6. DATA INGESTION INSTRUCTIONS (Database Specific Comments)
-- ------------------------------------------------------------------------------
/*
-- PostgreSQL Ingestion Example:
\copy netflix_raw FROM 'Dataset/netflix_titles_raw.csv' WITH (FORMAT csv, HEADER true);
\copy netflix_titles FROM 'Dataset/netflix_titles_cleaned.csv' WITH (FORMAT csv, HEADER true);

-- MySQL Ingestion Example:
LOAD DATA LOCAL INFILE 'Dataset/netflix_titles_cleaned.csv'
INTO TABLE netflix_titles
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;
*/
