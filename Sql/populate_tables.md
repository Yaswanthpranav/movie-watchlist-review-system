#set of all the queries ran to populate and form the tables


-- 1. Insert languages
INSERT INTO public.language (language_name)
VALUES
('English'),
('Hindi'),
('Telugu'),
('Tamil'),
('Malayalam'),
('Kannada'),
('Korean'),
('Japanese'),
('Spanish'),
('French');

-- 2. Insert genres
INSERT INTO public.genre (genre_name)
VALUES
('Action'),
('Adventure'),
('Comedy'),
('Drama'),
('Thriller'),
('Romance'),
('Science Fiction'),
('Fantasy'),
('Horror'),
('Mystery'),
('Animation'),
('Documentary'),
('Crime'),
('Family'),
('Musical');

-- 3. Insert streaming platforms
INSERT INTO public.streaming_platform (streaming_platform_name)
VALUES
('Netflix'),
('Amazon Prime Video'),
('Disney+ Hotstar'),
('JioHotstar'),
('SonyLIV'),
('ZEE5'),
('Apple TV+'),
('YouTube Movies');


ALTER TABLE public."user"
ADD COLUMN auth_user_id UUID UNIQUE
REFERENCES auth.users(id)
ON DELETE CASCADE;

ALTER TABLE public."user"
DROP COLUMN password_hash;

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    INSERT INTO public."user" (
        auth_user_id,
        username,
        email,
        create_date
    )
    VALUES (
        NEW.id,
        NEW.raw_user_meta_data ->> 'username',
        NEW.email,
        NOW()
    );

    RETURN NEW;
END;
$$;


CREATE OR REPLACE TRIGGER on_auth_user_created
AFTER INSERT ON auth.users
FOR EACH ROW
EXECUTE FUNCTION public.handle_new_user();


-- Enable Row Level Security on all CineTrack tables

ALTER TABLE public."user" ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.watchlist ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.watchlist_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reviews ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.movie ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.genre ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.language ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.movie_genre ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.movie_platform ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.streaming_platform ENABLE ROW LEVEL SECURITY;



-- View own watchlists
CREATE POLICY "Users can view their own watchlists"
ON public.watchlist
FOR SELECT
TO authenticated
USING (
    user_id IN (
        SELECT user_id
        FROM public."user"
        WHERE auth_user_id = (SELECT auth.uid())
    )
);

-- Create own watchlists
CREATE POLICY "Users can create their own watchlists"
ON public.watchlist
FOR INSERT
TO authenticated
WITH CHECK (
    user_id IN (
        SELECT user_id
        FROM public."user"
        WHERE auth_user_id = (SELECT auth.uid())
    )
);

-- Update own watchlists
CREATE POLICY "Users can update their own watchlists"
ON public.watchlist
FOR UPDATE
TO authenticated
USING (
    user_id IN (
        SELECT user_id
        FROM public."user"
        WHERE auth_user_id = (SELECT auth.uid())
    )
)
WITH CHECK (
    user_id IN (
        SELECT user_id
        FROM public."user"
        WHERE auth_user_id = (SELECT auth.uid())
    )
);

-- Delete own watchlists
CREATE POLICY "Users can delete their own watchlists"
ON public.watchlist
FOR DELETE
TO authenticated
USING (
    user_id IN (
        SELECT user_id
        FROM public."user"
        WHERE auth_user_id = (SELECT auth.uid())
    )
);


-- View items in own watchlists
CREATE POLICY "Users can view their own watchlist items"
ON public.watchlist_items
FOR SELECT
TO authenticated
USING (
    EXISTS (
        SELECT 1
        FROM public.watchlist w
        WHERE w.watchlist_id = watchlist_items.watchlist_id
        AND w.user_id IN (
            SELECT user_id
            FROM public."user"
            WHERE auth_user_id = (SELECT auth.uid())
        )
    )
);

-- Add items to own watchlists
CREATE POLICY "Users can add items to their own watchlists"
ON public.watchlist_items
FOR INSERT
TO authenticated
WITH CHECK (
    EXISTS (
        SELECT 1
        FROM public.watchlist w
        WHERE w.watchlist_id = watchlist_items.watchlist_id
        AND w.user_id IN (
            SELECT user_id
            FROM public."user"
            WHERE auth_user_id = (SELECT auth.uid())
        )
    )
);

-- Update items in own watchlists
CREATE POLICY "Users can update their own watchlist items"
ON public.watchlist_items
FOR UPDATE
TO authenticated
USING (
    EXISTS (
        SELECT 1
        FROM public.watchlist w
        WHERE w.watchlist_id = watchlist_items.watchlist_id
        AND w.user_id IN (
            SELECT user_id
            FROM public."user"
            WHERE auth_user_id = (SELECT auth.uid())
        )
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1
        FROM public.watchlist w
        WHERE w.watchlist_id = watchlist_items.watchlist_id
        AND w.user_id IN (
            SELECT user_id
            FROM public."user"
            WHERE auth_user_id = (SELECT auth.uid())
        )
    )
);

-- Delete items from own watchlists
CREATE POLICY "Users can delete their own watchlist items"
ON public.watchlist_items
FOR DELETE
TO authenticated
USING (
    EXISTS (
        SELECT 1
        FROM public.watchlist w
        WHERE w.watchlist_id = watchlist_items.watchlist_id
        AND w.user_id IN (
            SELECT user_id
            FROM public."user"
            WHERE auth_user_id = (SELECT auth.uid())
        )
    )
);


-- Everyone can read reviews
CREATE POLICY "Anyone can view reviews"
ON public.reviews
FOR SELECT
TO anon, authenticated
USING (true);

-- Authenticated users can create their own reviews
CREATE POLICY "Users can create their own reviews"
ON public.reviews
FOR INSERT
TO authenticated
WITH CHECK (
    user_id IN (
        SELECT user_id
        FROM public."user"
        WHERE auth_user_id = (SELECT auth.uid())
    )
);

-- Users can update their own reviews
CREATE POLICY "Users can update their own reviews"
ON public.reviews
FOR UPDATE
TO authenticated
USING (
    user_id IN (
        SELECT user_id
        FROM public."user"
        WHERE auth_user_id = (SELECT auth.uid())
    )
)
WITH CHECK (
    user_id IN (
        SELECT user_id
        FROM public."user"
        WHERE auth_user_id = (SELECT auth.uid())
    )
);

-- Users can delete their own reviews
CREATE POLICY "Users can delete their own reviews"
ON public.reviews
FOR DELETE
TO authenticated
USING (
    user_id IN (
        SELECT user_id
        FROM public."user"
        WHERE auth_user_id = (SELECT auth.uid())
    )
);


CREATE POLICY "Anyone can view movies"
ON public.movie
FOR SELECT TO anon, authenticated
USING (true);

CREATE POLICY "Anyone can view genres"
ON public.genre
FOR SELECT TO anon, authenticated
USING (true);

CREATE POLICY "Anyone can view languages"
ON public.language
FOR SELECT TO anon, authenticated
USING (true);

CREATE POLICY "Anyone can view movie genres"
ON public.movie_genre
FOR SELECT TO anon, authenticated
USING (true);

CREATE POLICY "Anyone can view movie platforms"
ON public.movie_platform
FOR SELECT TO anon, authenticated
USING (true);

CREATE POLICY "Anyone can view streaming platforms"
ON public.streaming_platform
FOR SELECT TO anon, authenticated
USING (true);

CREATE POLICY "Users can update their own profile"
ON public."user"
FOR UPDATE
TO authenticated
USING (
    auth_user_id = (SELECT auth.uid())
)
WITH CHECK (
    auth_user_id = (SELECT auth.uid())
);

INSERT INTO public."user" (
    username,
    email,
    create_date
)
SELECT
    'cine_user_' || LPAD(n::TEXT, 2, '0'),
    'cine_user_' || LPAD(n::TEXT, 2, '0') || '@example.com',
    NOW() - (n * INTERVAL '1 day')
FROM generate_series(2, 30) AS n;


WITH movie_data (
    title, release_yr, duration, language_name, description, age_rating
) AS (
    VALUES
    ('Inception', 2010, 148, 'English', 'A thief enters dreams to steal and plant ideas.', 'U/A'),
    ('Interstellar', 2014, 169, 'English', 'Explorers travel through space to find a new home for humanity.', 'U/A'),
    ('The Dark Knight', 2008, 152, 'English', 'Batman faces a dangerous criminal in Gotham City.', 'U/A'),
    ('The Shawshank Redemption', 1994, 142, 'English', 'Two prisoners develop a friendship over many years.', 'A'),
    ('The Grand Budapest Hotel', 2014, 99, 'English', 'A hotel concierge becomes involved in an unusual adventure.', 'U/A'),
    ('Parasite', 2019, 132, 'Korean', 'Two families from different social classes become connected.', 'A'),
    ('Train to Busan', 2016, 118, 'Korean', 'Passengers struggle to survive during a zombie outbreak.', 'A'),
    ('Oldboy', 2003, 120, 'Korean', 'A man seeks answers after being mysteriously imprisoned.', 'A'),
    ('Your Name', 2016, 106, 'Japanese', 'Two teenagers mysteriously begin experiencing each other lives.', 'U/A'),
    ('Spirited Away', 2001, 125, 'Japanese', 'A young girl enters a mysterious world of spirits.', 'U'),
    ('Weathering with You', 2019, 112, 'Japanese', 'A boy meets a girl who can influence the weather.', 'U/A'),
    ('3 Idiots', 2009, 170, 'Hindi', 'Three engineering students navigate college and friendship.', 'U/A'),
    ('Dangal', 2016, 161, 'Hindi', 'A former wrestler trains his daughters to compete in wrestling.', 'U/A'),
    ('Zindagi Na Milegi Dobara', 2011, 155, 'Hindi', 'Three friends take a road trip across Spain.', 'U/A'),
    ('Taare Zameen Par', 2007, 165, 'Hindi', 'An art teacher helps a young student discover his abilities.', 'U'),
    ('Queen', 2013, 146, 'Hindi', 'A young woman travels alone after her wedding plans change.', 'U/A'),
    ('Andhadhun', 2018, 139, 'Hindi', 'A pianist becomes involved in a mysterious crime.', 'A'),
    ('Drishyam', 2015, 163, 'Hindi', 'A family becomes involved in a complicated investigation.', 'U/A'),
    ('Jawan', 2023, 169, 'Hindi', 'A man takes on corruption and injustice.', 'U/A'),
    ('Laapataa Ladies', 2023, 124, 'Hindi', 'Two brides accidentally get separated during a train journey.', 'U/A'),
    ('RRR', 2022, 187, 'Telugu', 'Two revolutionaries form an extraordinary friendship.', 'U/A'),
    ('Baahubali: The Beginning', 2015, 159, 'Telugu', 'A young man discovers his royal origins.', 'U/A'),
    ('Eega', 2012, 145, 'Telugu', 'A man seeks justice after being reincarnated as a fly.', 'U/A'),
    ('Jersey', 2019, 157, 'Telugu', 'A former cricketer attempts to return to the sport.', 'U/A'),
    ('C/o Kancharapalem', 2018, 152, 'Telugu', 'Four stories explore love and relationships in a small town.', 'U/A'),
    ('Mahanati', 2018, 177, 'Telugu', 'A biographical drama about a celebrated Indian actress.', 'U/A'),
    ('Arjun Reddy', 2017, 186, 'Telugu', 'A medical student struggles with personal relationships.', 'A'),
    ('Hi Nanna', 2023, 155, 'Telugu', 'A father shares a story about love with his daughter.', 'U/A'),
    ('Vikram', 2022, 174, 'Tamil', 'A special investigation team uncovers a criminal network.', 'A'),
    ('96', 2018, 158, 'Tamil', 'Former classmates reunite after many years.', 'U'),
    ('Super Deluxe', 2019, 176, 'Tamil', 'Several unusual stories intersect over one eventful day.', 'A'),
    ('Soorarai Pottru', 2020, 153, 'Tamil', 'An ambitious man dreams of making air travel accessible.', 'U/A'),
    ('Kaithi', 2019, 145, 'Tamil', 'An ex-convict gets caught in a dangerous night-long mission.', 'A'),
    ('Asuran', 2019, 141, 'Tamil', 'A farmer fights to protect his family.', 'A'),
    ('Premam', 2015, 156, 'Malayalam', 'A young man experiences love at different stages of life.', 'U/A'),
    ('Drishyam', 2013, 164, 'Malayalam', 'A father tries to protect his family during an investigation.', 'U/A'),
    ('Bangalore Days', 2014, 171, 'Malayalam', 'Three cousins discover life and friendship in Bangalore.', 'U/A'),
    ('Kumbalangi Nights', 2019, 135, 'Malayalam', 'Four brothers navigate relationships and family life.', 'U/A'),
    ('Charlie', 2015, 130, 'Malayalam', 'A young woman follows clues left behind by an adventurous man.', 'U/A'),
    ('Manjummel Boys', 2024, 135, 'Malayalam', 'A group of friends face an unexpected challenge during a trip.', 'U/A')
)
INSERT INTO public.movie (
    title, release_yr, duration, language_id, description, age_rating
)
SELECT
    m.title,
    m.release_yr,
    m.duration,
    l.language_id,
    m.description,
    m.age_rating
FROM movie_data m
JOIN public.language l
    ON l.language_name = m.language_name;


WITH movie_genre_data (title, language_name, genre_name) AS (
    VALUES
    ('Inception', 'English', 'Science Fiction'),
    ('Inception', 'English', 'Thriller'),
    ('Interstellar', 'English', 'Science Fiction'),
    ('Interstellar', 'English', 'Adventure'),
    ('The Dark Knight', 'English', 'Action'),
    ('The Dark Knight', 'English', 'Crime'),
    ('The Shawshank Redemption', 'English', 'Drama'),
    ('The Shawshank Redemption', 'English', 'Crime'),
    ('The Grand Budapest Hotel', 'English', 'Comedy'),
    ('The Grand Budapest Hotel', 'English', 'Adventure'),

    ('Parasite', 'Korean', 'Thriller'),
    ('Parasite', 'Korean', 'Drama'),
    ('Train to Busan', 'Korean', 'Horror'),
    ('Train to Busan', 'Korean', 'Action'),
    ('Oldboy', 'Korean', 'Mystery'),
    ('Oldboy', 'Korean', 'Thriller'),

    ('Your Name', 'Japanese', 'Animation'),
    ('Your Name', 'Japanese', 'Romance'),
    ('Spirited Away', 'Japanese', 'Animation'),
    ('Spirited Away', 'Japanese', 'Fantasy'),
    ('Weathering with You', 'Japanese', 'Animation'),
    ('Weathering with You', 'Japanese', 'Fantasy'),

    ('3 Idiots', 'Hindi', 'Comedy'),
    ('3 Idiots', 'Hindi', 'Drama'),
    ('Dangal', 'Hindi', 'Drama'),
    ('Dangal', 'Hindi', 'Family'),
    ('Zindagi Na Milegi Dobara', 'Hindi', 'Adventure'),
    ('Zindagi Na Milegi Dobara', 'Hindi', 'Comedy'),
    ('Taare Zameen Par', 'Hindi', 'Drama'),
    ('Taare Zameen Par', 'Hindi', 'Family'),
    ('Queen', 'Hindi', 'Comedy'),
    ('Queen', 'Hindi', 'Drama'),
    ('Andhadhun', 'Hindi', 'Thriller'),
    ('Andhadhun', 'Hindi', 'Mystery'),
    ('Drishyam', 'Hindi', 'Thriller'),
    ('Drishyam', 'Hindi', 'Crime'),
    ('Jawan', 'Hindi', 'Action'),
    ('Jawan', 'Hindi', 'Thriller'),
    ('Laapataa Ladies', 'Hindi', 'Comedy'),
    ('Laapataa Ladies', 'Hindi', 'Drama'),

    ('RRR', 'Telugu', 'Action'),
    ('RRR', 'Telugu', 'Adventure'),
    ('Baahubali: The Beginning', 'Telugu', 'Action'),
    ('Baahubali: The Beginning', 'Telugu', 'Fantasy'),
    ('Eega', 'Telugu', 'Fantasy'),
    ('Eega', 'Telugu', 'Comedy'),
    ('Jersey', 'Telugu', 'Drama'),
    ('Jersey', 'Telugu', 'Family'),
    ('C/o Kancharapalem', 'Telugu', 'Drama'),
    ('C/o Kancharapalem', 'Telugu', 'Romance'),
    ('Mahanati', 'Telugu', 'Drama'),
    ('Mahanati', 'Telugu', 'Musical'),
    ('Arjun Reddy', 'Telugu', 'Drama'),
    ('Arjun Reddy', 'Telugu', 'Romance'),
    ('Hi Nanna', 'Telugu', 'Drama'),
    ('Hi Nanna', 'Telugu', 'Family'),

    ('Vikram', 'Tamil', 'Action'),
    ('Vikram', 'Tamil', 'Thriller'),
    ('96', 'Tamil', 'Romance'),
    ('96', 'Tamil', 'Drama'),
    ('Super Deluxe', 'Tamil', 'Drama'),
    ('Super Deluxe', 'Tamil', 'Thriller'),
    ('Soorarai Pottru', 'Tamil', 'Drama'),
    ('Soorarai Pottru', 'Tamil', 'Biography'),
    ('Kaithi', 'Tamil', 'Action'),
    ('Kaithi', 'Tamil', 'Thriller'),
    ('Asuran', 'Tamil', 'Action'),
    ('Asuran', 'Tamil', 'Drama'),

    ('Premam', 'Malayalam', 'Romance'),
    ('Premam', 'Malayalam', 'Comedy'),
    ('Drishyam', 'Malayalam', 'Thriller'),
    ('Drishyam', 'Malayalam', 'Crime'),
    ('Bangalore Days', 'Malayalam', 'Comedy'),
    ('Bangalore Days', 'Malayalam', 'Romance'),
    ('Kumbalangi Nights', 'Malayalam', 'Drama'),
    ('Kumbalangi Nights', 'Malayalam', 'Family'),
    ('Charlie', 'Malayalam', 'Adventure'),
    ('Charlie', 'Malayalam', 'Drama'),
    ('Manjummel Boys', 'Malayalam', 'Adventure'),
    ('Manjummel Boys', 'Malayalam', 'Thriller')
)
INSERT INTO public.movie_genre (movie_id, genre_id)
SELECT
    m.movie_id,
    g.genre_id
FROM movie_genre_data mg
JOIN public.movie m
    ON m.title = mg.title
JOIN public.language l
    ON l.language_id = m.language_id
    AND l.language_name = mg.language_name
JOIN public.genre g
    ON g.genre_name = mg.genre_name;


WITH platform_data (title, language_name, platform_name) AS (
    VALUES
    ('Inception', 'English', 'Netflix'),
    ('Inception', 'English', 'Amazon Prime Video'),
    ('Interstellar', 'English', 'Netflix'),
    ('Interstellar', 'English', 'Apple TV+'),
    ('The Dark Knight', 'English', 'Amazon Prime Video'),
    ('The Dark Knight', 'English', 'YouTube Movies'),
    ('The Shawshank Redemption', 'English', 'Netflix'),
    ('The Grand Budapest Hotel', 'English', 'Disney+ Hotstar'),

    ('Parasite', 'Korean', 'Netflix'),
    ('Parasite', 'Korean', 'Amazon Prime Video'),
    ('Train to Busan', 'Korean', 'Netflix'),
    ('Oldboy', 'Korean', 'Amazon Prime Video'),

    ('Your Name', 'Japanese', 'Netflix'),
    ('Your Name', 'Japanese', 'Amazon Prime Video'),
    ('Spirited Away', 'Japanese', 'Netflix'),
    ('Weathering with You', 'Japanese', 'YouTube Movies'),

    ('3 Idiots', 'Hindi', 'Amazon Prime Video'),
    ('3 Idiots', 'Hindi', 'YouTube Movies'),
    ('Dangal', 'Hindi', 'Disney+ Hotstar'),
    ('Zindagi Na Milegi Dobara', 'Hindi', 'Netflix'),
    ('Taare Zameen Par', 'Hindi', 'Disney+ Hotstar'),
    ('Queen', 'Hindi', 'Netflix'),
    ('Andhadhun', 'Hindi', 'Amazon Prime Video'),
    ('Drishyam', 'Hindi', 'Netflix'),
    ('Jawan', 'Hindi', 'Netflix'),
    ('Laapataa Ladies', 'Hindi', 'Amazon Prime Video'),

    ('RRR', 'Telugu', 'Netflix'),
    ('RRR', 'Telugu', 'ZEE5'),
    ('Baahubali: The Beginning', 'Telugu', 'Netflix'),
    ('Baahubali: The Beginning', 'Telugu', 'Amazon Prime Video'),
    ('Eega', 'Telugu', 'YouTube Movies'),
    ('Jersey', 'Telugu', 'Amazon Prime Video'),
    ('C/o Kancharapalem', 'Telugu', 'Netflix'),
    ('Mahanati', 'Telugu', 'Amazon Prime Video'),
    ('Arjun Reddy', 'Telugu', 'Amazon Prime Video'),
    ('Hi Nanna', 'Telugu', 'Netflix'),

    ('Vikram', 'Tamil', 'Disney+ Hotstar'),
    ('Vikram', 'Tamil', 'Amazon Prime Video'),
    ('96', 'Tamil', 'Amazon Prime Video'),
    ('Super Deluxe', 'Tamil', 'Netflix'),
    ('Soorarai Pottru', 'Tamil', 'Amazon Prime Video'),
    ('Kaithi', 'Tamil', 'Disney+ Hotstar'),
    ('Asuran', 'Tamil', 'Amazon Prime Video'),

    ('Premam', 'Malayalam', 'Amazon Prime Video'),
    ('Drishyam', 'Malayalam', 'Amazon Prime Video'),
    ('Drishyam', 'Malayalam', 'YouTube Movies'),
    ('Bangalore Days', 'Malayalam', 'Disney+ Hotstar'),
    ('Kumbalangi Nights', 'Malayalam', 'Amazon Prime Video'),
    ('Charlie', 'Malayalam', 'Netflix'),
    ('Manjummel Boys', 'Malayalam', 'Disney+ Hotstar')
)
INSERT INTO public.movie_platform (movie_id, platform_id)
SELECT
    m.movie_id,
    sp.streaming_platform_id
FROM platform_data pd
JOIN public.movie m
    ON m.title = pd.title
JOIN public.language l
    ON l.language_id = m.language_id
    AND l.language_name = pd.language_name
JOIN public.streaming_platform sp
    ON sp.streaming_platform_name = pd.platform_name;


WITH ranked_users AS (
    SELECT
        user_id,
        ROW_NUMBER() OVER (ORDER BY user_id) AS user_rank
    FROM public."user"
),
watchlist_data AS (
    -- Every user gets a first watchlist
    SELECT
        user_id,
        'My Watchlist' AS watchlist_name,
        'Movies I want to watch or keep track of.' AS notes
    FROM ranked_users

    UNION ALL

    -- The first five users get an additional watchlist
    SELECT
        user_id,
        'Weekend Picks' AS watchlist_name,
        'Movies selected for weekend viewing.' AS notes
    FROM ranked_users
    WHERE user_rank <= 5
)
INSERT INTO public.watchlist (
    user_id,
    watchlist_name,
    notes,
    create_date
)
SELECT
    user_id,
    watchlist_name,
    notes,
    NOW()
FROM watchlist_data;


WITH ranked_watchlists AS (
    SELECT
        watchlist_id,
        ROW_NUMBER() OVER (ORDER BY watchlist_id) AS watchlist_rank
    FROM public.watchlist
),
ranked_movies AS (
    SELECT
        movie_id,
        ROW_NUMBER() OVER (ORDER BY movie_id) AS movie_rank
    FROM public.movie
),
item_data AS (
    SELECT
        w.watchlist_id,
        m.movie_id,
        w.watchlist_rank,
        m.movie_rank,
        ROW_NUMBER() OVER (
            ORDER BY w.watchlist_rank, m.movie_rank
        ) AS item_number
    FROM ranked_watchlists w
    CROSS JOIN ranked_movies m
)
INSERT INTO public.watchlist_items (
    watchlist_id,
    movie_id,
    added_date,
    status
)
SELECT
    watchlist_id,
    movie_id,
    CURRENT_DATE - (item_number % 90)::INTEGER,
    CASE
        WHEN item_number % 3 = 0 THEN 'COMPLETED'
        WHEN item_number % 3 = 1 THEN 'PLANNED'
        ELSE 'WATCHING'
    END
FROM item_data
WHERE item_number <= 100;


WITH ranked_pairs AS (
    SELECT
        u.user_id,
        m.movie_id,
        ROW_NUMBER() OVER (
            ORDER BY u.user_id, m.movie_id
        ) AS review_number
    FROM public."user" u
    CROSS JOIN public.movie m
)
INSERT INTO public.reviews (
    user_id,
    movie_id,
    platform_id,
    rating,
    review_text,
    reviewed_on
)
SELECT
    rp.user_id,
    rp.movie_id,

    CASE
        WHEN rp.review_number % 2 = 0 THEN (
            SELECT mp.platform_id
            FROM public.movie_platform mp
            WHERE mp.movie_id = rp.movie_id
            ORDER BY mp.platform_id
            LIMIT 1
        )
        ELSE NULL
    END,

    (1 + (rp.review_number % 5))::DECIMAL(2,1),

    CASE
        WHEN rp.review_number % 5 = 0
            THEN 'An excellent movie with a memorable story.'
        WHEN rp.review_number % 5 = 1
            THEN 'Really enjoyed the performances and direction.'
        WHEN rp.review_number % 5 = 2
            THEN 'A good movie with some interesting moments.'
        WHEN rp.review_number % 5 = 3
            THEN 'The story was engaging and entertaining.'
        ELSE
            'An average experience, but worth watching.'
    END,

    CURRENT_DATE - (rp.review_number % 120)::INTEGER

FROM ranked_pairs rp
WHERE rp.review_number <= 125;

#tocheck the tables
SELECT 'user' AS table_name, COUNT(*) AS total FROM public."user"
UNION ALL
SELECT 'watchlist', COUNT(*) FROM public.watchlist
UNION ALL
SELECT 'watchlist_items', COUNT(*) FROM public.watchlist_items
UNION ALL
SELECT 'movie', COUNT(*) FROM public.movie
UNION ALL
SELECT 'language', COUNT(*) FROM public.language
UNION ALL
SELECT 'genre', COUNT(*) FROM public.genre
UNION ALL
SELECT 'movie_genre', COUNT(*) FROM public.movie_genre
UNION ALL
SELECT 'reviews', COUNT(*) FROM public.reviews
UNION ALL
SELECT 'streaming_platform', COUNT(*) FROM public.streaming_platform
UNION ALL
SELECT 'movie_platform', COUNT(*) FROM public.movie_platform
ORDER BY table_name;