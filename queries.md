# CineTrack – SQL Query Documentation

### Query 01: Display All Movies
SELECT
    m.movie_id,
    m.title,
    m.release_yr,
    m.duration,
    m.description,
    m.age_rating,
    l.language_name
FROM movie m
JOIN language l
    ON m.language_id = l.language_id
ORDER BY m.title ASC

### Query 02: Search Movies by Title
SELECT *
FROM movie
WHERE title ILIKE '%' || $1 || '%'
ORDER BY title;

### Query 03: Genre Dropdown
SELECT
    genre_id,
    genre_name
FROM genre
ORDER BY genre_name;

### Query 04: Streaming Platform Dropdown
SELECT
    streaming_platform_id,
    streaming_platform_name
FROM streaming_platform
ORDER BY streaming_platform_name;

### Query 05: Streaming Platform Dropdown
### Query 04: Streaming Platform Dropdown
### Query 04: Streaming Platform Dropdown
### Query 04: Streaming Platform Dropdown
### Query 04: Streaming Platform Dropdown

Continue with the remaining movie-related queries.

## 2. User Profile Management

### Query 10: Retrieve User Profile
```sql
-- Paste your actual SQL query here
```

### Query 11: Create User Profile
```sql
-- Paste your actual SQL query here
```

## 3. Watchlist Management
### Query 04: Streaming Platform Dropdown
### Query 04: Streaming Platform Dropdown
### Query 04: Streaming Platform Dropdown
### Query 04: Streaming Platform Dropdown
### Query 04: Streaming Platform Dropdown
### Query 04: Streaming Platform Dropdown

Include queries for creating watchlists, adding and removing movies, displaying watchlist contents and updating status.

## 4. Review Management

Include queries for submitting, editing and deleting reviews.

## 5. Additional Database Features

Include:
- Average Ratings VIEW
- Review Timestamp
