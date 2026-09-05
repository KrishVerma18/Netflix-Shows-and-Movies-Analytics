# Netflix Dataset Data Dictionary

This document outlines the schema, column definitions, data types, null counts, and transformation logic applied to the Netflix Movies and TV Shows dataset (`netflix_titles_raw.csv` and `netflix_titles_cleaned.csv`).

---

## 1. Overview
- **Raw Records**: 8,807 titles
- **Cleaned Records**: 8,807 titles (100% catalog retention; zero rows dropped)
- **Source**: Public Kaggle Netflix Movies & TV Shows Dataset (collected via Netflix API / public metadata)
- **Temporal Coverage**: Content released from 1925 through 2021; added to Netflix from 2008 through 2021

---

## 2. Column Specifications

| Column Name | Raw Type | Cleaned Type | Null Count (Cleaned) | Description & Transformation Notes |
| :--- | :--- | :--- | :--- | :--- |
| `show_id` | String | VARCHAR(10) | 0 | Unique identifier for each title (e.g., `s1`, `s2`, ... `s8807`). Serves as Primary Key. |
| `type` | String | VARCHAR(10) | 0 | Content category: strictly classified into `Movie` (6,131 titles / 69.6%) or `TV Show` (2,676 titles / 30.4%). |
| `title` | String | VARCHAR(255) | 0 | Official title of the movie or television show. Trimmed of leading/trailing whitespace. |
| `director` | String | VARCHAR(255) | 0 | Director(s) of the content. 2,634 raw missing values imputed with `'Unknown'`. Comma-separated for multiple directors. |
| `cast` | String | TEXT | 0 | Cast members/actors featured. 825 raw missing values imputed with `'Unknown'`. Comma-separated for multiple actors. |
| `country` | String | VARCHAR(255) | 0 | Country or countries of production. 831 raw missing values imputed with `'Unknown'`. Comma-separated for co-productions. |
| `primary_country` | *New* | VARCHAR(100) | 0 | **Engineered**: The first/lead production country extracted from the `country` field. Facilitates top-level geographic analysis. |
| `date_added` | String | DATE (ISO) | 10 | Date content was uploaded to Netflix. Standardized from diverse strings (e.g. "September 25, 2021") to ISO format `YYYY-MM-DD`. |
| `year_added` | *New* | INT | 10 | **Engineered**: Calendar year content was added to Netflix (2008–2021). |
| `month_added` | *New* | INT | 10 | **Engineered**: Numerical month content was added to Netflix (1–12). |
| `month_name_added` | *New* | VARCHAR(20) | 10 | **Engineered**: Full month name (e.g., "September") for seasonal trend analysis. |
| `release_year` | Integer | INT | 0 | The original theatrical or broadcast release year of the title (1925–2021). |
| `rating` | String | VARCHAR(10) | 0 | Content rating / age suitability certification (e.g., `TV-MA`, `TV-14`, `R`, `PG-13`, `PG`, `TV-Y7`, `TV-Y`, `TV-G`, `G`, `NR`). 3 misplaced records corrected; missing values imputed as `'NR'` (Not Rated). |
| `rating_category` | *New* | VARCHAR(50) | 0 | **Engineered**: Consolidated audience maturity bucket: `Adults (18+)`, `Teens (13-17)`, `Older Kids (7-12)`, `Kids (All Ages)`, `Unrated / NR`. |
| `duration` | String | VARCHAR(50) | 0 | Textual duration representation (e.g., "90 min" for Movies, "2 Seasons" for TV Shows). Shifted values in 3 rows restored. |
| `duration_minutes` | *New* | INT | 2,676 | **Engineered**: Parsed integer duration in minutes for Movies (NULL for TV Shows). Enables numerical runtime aggregations (AVG, MIN, MAX, standard deviation). |
| `duration_seasons` | *New* | INT | 6,131 | **Engineered**: Parsed integer season count for TV Shows (NULL for Movies). Enables distribution analysis of series longevity. |
| `listed_in` | String | VARCHAR(255) | 0 | Comma-separated list of genres and categories assigned by Netflix (e.g., "Dramas, International Movies"). |
| `primary_genre` | *New* | VARCHAR(100) | 0 | **Engineered**: Lead genre extracted from `listed_in` for clean macro-level categorization without double-counting. |
| `description` | String | TEXT | 0 | Brief synopsis / editorial summary of the title. Whitespace trimmed. |

---

## 3. Data Cleaning Log & Rules Summary

1. **Duration & Rating Column Shift Fix**:
   - In rows `s5542` (*Louis C.K. 2017*), `s5795` (*Louis C.K.: Hilarious*), and `s5814` (*Louis C.K.: Live at the Comedy Store*), the values `"74 min"`, `"84 min"`, and `"66 min"` were accidentally stored in the `rating` column while `duration` was `NaN`.
   - *Action*: Shifted minute strings to `duration`, extracted `duration_minutes`, and updated `rating` to `'NR'`.
2. **Missing Text Value Imputation**:
   - `director` (2,634 missing), `cast` (825 missing), and `country` (831 missing) were populated with `'Unknown'` to retain 100% of rows for aggregate analysis while remaining filterable.
3. **Date Standardization**:
   - String dates with inconsistent month spacing were parsed into standard `YYYY-MM-DD` dates.
4. **Relational Normalization Tables**:
   - Created 1-to-many relationship mapping tables for deep SQL querying:
     - `relational_directors` (show_id, director)
     - `relational_cast` (show_id, actor)
     - `relational_countries` (show_id, country)
     - `relational_genres` (show_id, genre)
