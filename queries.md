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

### Query 05: Rating Handeling
SELECT
    m.movie_id,
    m.title,
    m.release_yr,
    COALESCE(AVG(r.rating), 0) AS avg_rating

FROM movie m

LEFT JOIN reviews r
    ON m.movie_id = r.movie_id

GROUP BY
    m.movie_id,
    m.title,
    m.release_yr

HAVING
    $1::NUMERIC IS NULL
    OR AVG(r.rating) = $1

ORDER BY
    avg_rating DESC;

### Query 06: Year
SELECT
    m.movie_id,
    m.title,
    m.release_yr,
    m.duration,
    m.age_rating,
    l.language_name

FROM movie m

JOIN language l
    ON m.language_id = l.language_id

WHERE
    (NULLIF($1, '') IS NULL
     OR m.title ILIKE '%' || $1 || '%')

    AND ($2::INT IS NULL
         OR EXISTS (
             SELECT 1
             FROM movie_genre mg
             WHERE mg.movie_id = m.movie_id
             AND mg.genre_id = $2
         ))

    AND ($3::INT IS NULL
         OR EXISTS (
             SELECT 1
             FROM movie_platform mp
             WHERE mp.movie_id = m.movie_id
             AND mp.platform_id = $3
         ))

    AND ($4::INT IS NULL
         OR m.release_yr = $4);

### Query 07: Combined Display
SELECT
    m.movie_id,
    m.title,
    m.release_yr,
    m.duration,
    m.age_rating,
    l.language_name,
    COALESCE(mr.average_rating, 0) AS avg_rating,
    COALESCE(mr.total_reviews, 0) AS review_count

FROM movie m

JOIN language l
    ON m.language_id = l.language_id

LEFT JOIN movie_rating_summary mr
    ON m.movie_id = mr.movie_id

WHERE
    ($1::TEXT IS NULL OR m.title ILIKE '%' || $1 || '%')

    AND (
        $2::INT IS NULL
        OR EXISTS (
            SELECT 1
            FROM movie_genre mg
            WHERE mg.movie_id = m.movie_id
            AND mg.genre_id = $2
        )
    )

    AND (
        $3::INT IS NULL
        OR EXISTS (
            SELECT 1
            FROM movie_platform mp
            WHERE mp.movie_id = m.movie_id
            AND mp.platform_id = $3
        )
    )

    AND (
        $4::NUMERIC IS NULL
        OR mr.average_rating >= $4
    )

    AND (
        $5::INT IS NULL
        OR m.release_yr = $5
    )

ORDER BY

    CASE
        WHEN $6 = 'title_asc' THEN m.title
    END ASC,

    CASE
        WHEN $6 = 'title_desc' THEN m.title
    END DESC,

    CASE
        WHEN $6 = 'newest' THEN m.release_yr
    END DESC NULLS LAST,

    CASE
        WHEN $6 = 'oldest' THEN m.release_yr
    END ASC NULLS LAST,

    CASE
        WHEN $6 = 'highest_rated' THEN mr.average_rating
    END DESC NULLS LAST,

    CASE
        WHEN $6 = 'lowest_rated' THEN mr.average_rating
    END ASC NULLS LAST,

    CASE
        WHEN $6 = 'most_reviewed' THEN mr.total_reviews
    END DESC NULLS LAST,

    m.title ASC;

### Query 08: Top Rated
SELECT
    movie_id,
    title,
    release_yr,
    average_rating,
    total_reviews

FROM movie_rating_summary

WHERE total_reviews > 0

ORDER BY
    average_rating DESC,
    total_reviews DESC,
    title ASC

LIMIT 10;

### Query 09: Movie Details
WITH movie_genres AS (
    SELECT
        mg.movie_id,
        JSON_AGG(
            JSON_BUILD_OBJECT(
                'genre_id', g.genre_id,
                'genre_name', g.genre_name
            )
            ORDER BY g.genre_name
        ) AS genres

    FROM movie_genre mg

    JOIN genre g
        ON mg.genre_id = g.genre_id

    GROUP BY mg.movie_id
),

movie_platforms AS (
    SELECT
        mp.movie_id,
        JSON_AGG(
            JSON_BUILD_OBJECT(
                'platform_id', sp.streaming_platform_id,
                'platform_name', sp.streaming_platform_name
            )
            ORDER BY sp.streaming_platform_name
        ) AS platforms

    FROM movie_platform mp

    JOIN streaming_platform sp
        ON mp.platform_id = sp.streaming_platform_id

    GROUP BY mp.movie_id
),

movie_reviews AS (
    SELECT
        r.movie_id,

        JSON_AGG(
            JSON_BUILD_OBJECT(
                'review_id', r.review_id,
                'username', u.username,
                'rating', r.rating,
                'review_text', r.review_text,
                'reviewed_on', r.reviewed_on,
                'platform', sp.streaming_platform_name
            )
            ORDER BY r.reviewed_on DESC
        ) AS reviews,

        ROUND(AVG(r.rating), 2) AS average_rating,
        COUNT(*) AS total_reviews

    FROM reviews r

    JOIN "user" u
        ON r.user_id = u.user_id

    LEFT JOIN streaming_platform sp
        ON r.platform_id = sp.streaming_platform_id

    GROUP BY r.movie_id
)

SELECT
    m.movie_id,
    m.title,
    m.release_yr,
    m.duration,
    m.description AS plot,
    m.age_rating,
    l.language_name,

    COALESCE(mg.genres, '[]'::JSON) AS genres,

    COALESCE(mp.platforms, '[]'::JSON) AS streaming_platforms,

    COALESCE(mr.reviews, '[]'::JSON) AS reviews,

    COALESCE(mr.average_rating, 0) AS average_rating,
    COALESCE(mr.total_reviews, 0) AS total_reviews

FROM movie m

JOIN language l
    ON m.language_id = l.language_id

LEFT JOIN movie_genres mg
    ON m.movie_id = mg.movie_id

LEFT JOIN movie_platforms mp
    ON m.movie_id = mp.movie_id

LEFT JOIN movie_reviews mr
    ON m.movie_id = mr.movie_id

WHERE m.movie_id = $1;

### Query 10: Retrieve User Profile
SELECT
    user_id,
    username,
    email,
    create_date
FROM "user"
WHERE auth_user_id = auth.uid();

### Query 11: Create User Profile
INSERT INTO "user" (
    auth_user_id,
    username,
    email
)
VALUES (
    auth.uid(),
    $1,
    $2
);

## 3. Watchlist Management
### Query 012: Retrieve user watchlist after login
SELECT
    watchlist_id,
    watchlist_name,
    notes,
    create_date
FROM watchlist
WHERE user_id = (
    SELECT user_id
    FROM "user"
    WHERE auth_user_id = auth.uid()
);

### Query 013: Display Movies in Watchlist
SELECT
    wi.watchlist_item_id,
    m.movie_id,
    m.title,
    m.release_yr,
    wi.added_date,
    wi.status

FROM watchlist_items wi

JOIN watchlist w
    ON wi.watchlist_id = w.watchlist_id

JOIN movie m
    ON wi.movie_id = m.movie_id

JOIN "user" u
    ON w.user_id = u.user_id

WHERE
    u.auth_user_id = auth.uid()
    AND w.watchlist_id = $1

ORDER BY wi.added_date DESC;

### Query 014: Add to watchlist
INSERT INTO watchlist_items (
    watchlist_id,
    movie_id,
    status
)
VALUES (
    $1,
    $2,
    'PLANNED'
);

### Query 015: Remove from watchlist
DELETE FROM watchlist_items
WHERE watchlist_id = $1
AND movie_id = $2;

### Query 016: Update status
UPDATE watchlist_items
SET status = 'COMPLETED'
WHERE watchlist_id = $1
AND movie_id = $2;
### Query 017: Create watchlist
INSERT INTO watchlist (
    user_id,
    watchlist_name,
    notes
)
VALUES (
    $1,
    $2,
    $3
);

### Query 018: Submit review
INSERT INTO reviews (
    user_id,
    movie_id,
    platform_id,
    rating,
    review_text
)
VALUES (
    $1,
    $2,
    $3,
    $4,
    $5
);

### Query 019: Edit Review
UPDATE reviews
SET
    rating = $1,
    review_text = $2,
    reviewed_on = CURRENT_TIMESTAMP
WHERE
    user_id = $3
    AND movie_id = $4;

### Query 020: Delete review
DELETE FROM reviews
WHERE user_id = $1
AND movie_id = $2;

### Query 021: Average rating (VIEW)
CREATE VIEW movie_rating_summary AS
SELECT
    m.movie_id,
    m.title,
    m.release_yr,
    ROUND(AVG(r.rating), 2) AS average_rating,
    COUNT(r.review_id) AS total_reviews
FROM movie m
LEFT JOIN reviews r
    ON m.movie_id = r.movie_id
GROUP BY
    m.movie_id,
    m.title,
    m.release_yr;

### Query 022: Review Timestamp
CREATE OR REPLACE FUNCTION update_review_timestamp()
RETURNS TRIGGER AS $$

BEGIN
    NEW.reviewed_on = CURRENT_TIMESTAMP;
    RETURN NEW;

END;

$$ LANGUAGE plpgsql;


CREATE TRIGGER review_timestamp_trigger

BEFORE UPDATE ON reviews

FOR EACH ROW

EXECUTE FUNCTION update_review_timestamp();
