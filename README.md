# CineTrack — Movie Watchlist & Community Review Platform

> A database-driven web application for discovering movies, managing personal watchlists, tracking viewing history, and sharing ratings and reviews.

**Project type:** DBMS course project  
**Status:** In development / planned implementation  
**Primary focus:** Relational database design, normalization, integrity constraints, and SQL query implementation

---

## Table of Contents

- [Project Overview](#project-overview)
- [Objectives](#objectives)
- [Planned Features](#planned-features)
- [Team Information and Contributions](#team-information-and-contributions)
- [Technology Stack](#technology-stack)
- [System Architecture](#system-architecture)
- [Database Design](#database-design)
- [Key Database Rules](#key-database-rules)
- [Application Workflows](#application-workflows)
- [Configuration](#configuration)
- [Planned SQL and DBMS Demonstrations](#planned-sql-and-dbms-demonstrations)


---

## Project Overview

**CineTrack** is a planned full-stack application that helps users organize their movie-watching activities in one place. Users will be able to explore a movie catalogue, filter films by language and genre, save movies to a personal watchlist, record completed viewings, and publish ratings and written reviews.

The project is being developed as a Database Management Systems (DBMS) course project. Its main goal is to demonstrate how a well-designed relational database can support a practical application through appropriate schema design, normalization, primary and foreign keys, integrity constraints, transactions, and meaningful SQL queries.

The initial catalogue is intended to support **English, Hindi, and Telugu** movies. This scope can be extended as the project develops.

## Objectives

- Design a clear relational schema with appropriate entities, relationships, and keys.
- Reduce avoidable data redundancy through normalization.
- Enforce data correctness with primary keys, foreign keys, `CHECK`, and `UNIQUE` constraints.
- Support movie discovery through title, language, genre, and rating-based queries.
- Implement watchlist, viewing-history, and review workflows.
- Demonstrate useful SQL features such as joins, aggregation, subqueries, common table expressions (CTEs), and window functions.
- Build a web interface connected to a backend API and PostgreSQL database.

## Planned Features

- **Movie catalogue:** Browse movie titles and view details such as synopsis, release year, runtime, language, genres, and cast.
- **Search and filters:** Search by title and filter by language, genre, or other supported criteria.
- **Personal watchlist:** Add movies to a watchlist and remove them when no longer needed.
- **Viewing history:** Record movies a user has watched, including the date and time of the viewing.
- **Community reviews:** Submit a rating from 1 to 5 and optional written feedback for a movie.
- **Rating summaries:** Display aggregate ratings, such as the average rating and number of reviews.
- **Relational integrity:** Use constraints and transactions to maintain consistent data.

> These are project goals, not a claim that every feature is already implemented. See [Project Progress](#project-progress) for the current checklist.

## Team Information and Contributions

Replace the placeholders below with the team's official details before submission.

| Team Member | Student ID | Responsibilities and Contributions |
|---|---|---|
| **[Your Name]** | `[Your Student ID]` | Repository setup, Git/GitHub coordination, README maintenance, and project integration. |
| **[Teammate 1 Name]** | `[Student ID]` | Requirements analysis, ER/EER diagram, relationship cardinalities, and business rules. |
| **[Teammate 2 Name]** | `[Student ID]` | Relational schema, normalization analysis, keys, and integrity constraints. |
| **[Teammate 3 Name]** | `[Student ID]` | Application architecture, API planning, frontend design, and workflow documentation. |

Update the responsibilities to reflect each member's actual contribution. If your team has a different number of members, add or remove rows.

## Technology Stack

The following stack is proposed for the project. Update this section if the implementation changes.

| Layer | Technology | Purpose |
|---|---|---|
| Database | PostgreSQL 15 or later | Relational storage, constraints, queries, and transactions |
| Backend | Python 3.10 or later with Flask | Application logic and REST API |
| Database access | `psycopg2-binary` or SQLAlchemy | Connecting the Python application to PostgreSQL |
| Frontend | React with Vite | Interactive user interface |
| Styling | Tailwind CSS or standard CSS | Layout and visual styling |
| Version control | Git and GitHub | Source control and team collaboration |

Choose either `psycopg2-binary` or SQLAlchemy based on the project's implementation; both are listed here as options, not as a requirement to use both.

## System Architecture

CineTrack is planned around a three-tier architecture:

```text
┌───────────────────────────────────────────────┐
│                 Frontend                      │
│            React + Vite + CSS                 │
│  Catalogue · Search · Watchlist · Reviews     │
└──────────────────────┬────────────────────────┘
                       │ HTTP requests / JSON
                       ▼
┌───────────────────────────────────────────────┐
│                 Backend                       │
│                Python + Flask                 │
│       API endpoints · Validation · Logic      │
└──────────────────────┬────────────────────────┘
                       │ Database connection
                       ▼
┌───────────────────────────────────────────────┐
│                 Database                      │
│                 PostgreSQL                    │
│       Tables · Keys · Constraints · SQL       │
└───────────────────────────────────────────────┘
```

The frontend will send requests to the Flask API. The backend will validate input, execute database operations, and return responses. PostgreSQL will store the persistent application data and enforce relational integrity.

## Database Design

The proposed logical design contains **10 relations**. Final column definitions and constraints should be documented in `database/schema.sql` and kept consistent with the ER diagram and application code.

| Relation | Purpose | Important keys / relationships |
|---|---|---|
| `Users` | Stores user profile and account information. | `user_id` (PK) |
| `Languages` | Catalogue of supported languages. | `language_id` (PK) |
| `Movies` | Stores movie metadata such as title, synopsis, runtime, and release year. | `movie_id` (PK); `language_id` (FK → `Languages.language_id`) |
| `Genres` | Master list of movie genres. | `genre_id` (PK) |
| `MovieGenres` | Connects movies and genres in a many-to-many relationship. | Composite PK (`movie_id`, `genre_id`); both columns are FKs |
| `Actors` | Stores performer information. | `actor_id` (PK) |
| `MovieActors` | Connects actors and movies in a many-to-many relationship. | Composite PK (`movie_id`, `actor_id`); both columns are FKs |
| `WatchlistItems` | Records movies saved by users. | Composite PK (`user_id`, `movie_id`); both columns are FKs |
| `ViewingHistory` | Records movies watched by users and viewing timestamps. | `history_id` (PK); `user_id` and `movie_id` are FKs |
| `Reviews` | Stores user ratings and review text for movies. | `review_id` (PK); `user_id` and `movie_id` are FKs |

**Key:** PK = primary key; FK = foreign key. The table names above use the proposed capitalization. PostgreSQL folds unquoted identifiers to lowercase, so use one naming convention consistently in the SQL files and application code.

### Important relationship notes

- One language can be associated with many movies.
- A movie can belong to many genres, and a genre can be assigned to many movies; `MovieGenres` resolves this many-to-many relationship.
- A movie can feature many actors, and an actor can appear in many movies; `MovieActors` resolves this many-to-many relationship.
- Users can save many movies, and each movie can appear in many users' watchlists; `WatchlistItems` resolves this relationship.
- Users can have multiple viewing-history records over time if repeat viewings are supported.
- The proposed rule `UNIQUE (user_id, movie_id)` on `Reviews` allows at most one review per user per movie. If review editing or multiple reviews per viewing are required, revisit this rule before implementation.

## Key Database Rules

The following rules are planned for implementation in the schema:

- Every relation should have a primary key.
- Foreign keys should reference existing parent records and prevent invalid relationships.
- Review ratings must be integers from 1 through 5, enforced with a `CHECK` constraint such as `CHECK (rating BETWEEN 1 AND 5)`.
- If users may submit only one review per movie, enforce `UNIQUE (user_id, movie_id)` in `Reviews`.
- Composite keys on junction tables should prevent duplicate movie–genre, movie–actor, and user–watchlist pairs.
- Required fields should use `NOT NULL` where appropriate.
- Multi-step operations, such as recording a viewing and updating related state, should use transactions where consistency requires all steps to succeed or fail together.
- Passwords must never be stored as plain text; store a securely hashed password if account authentication is implemented.

## Application Workflows

### 1. Movie discovery

1. A user enters a title or selects a genre or language filter.
2. The frontend sends the criteria to the backend API.
3. The backend runs a parameterized SQL query joining the relevant catalogue tables.
4. The results may include each movie's average review rating and review count.

### 2. Watchlist management and viewing history

1. A user adds a movie to their watchlist.
2. The backend inserts the user–movie pair into `WatchlistItems`.
3. When the user marks a movie as watched, the backend records the viewing in `ViewingHistory`.
4. Related database changes are handled in a transaction when they must remain consistent.

### 3. Review publishing

1. A user submits a rating from 1 to 5 and optional written feedback.
2. The backend validates the request and sends a parameterized insert or update to PostgreSQL.
3. Database constraints reject invalid ratings and duplicate reviews where the one-review-per-user-per-movie rule applies.
4. The movie page displays the updated aggregate rating and review count.




## Planned SQL and DBMS Demonstrations

The final project is intended to demonstrate a variety of database concepts, subject to implementation and course requirements:

- **Joins:** Retrieve movies with language, genre, and cast details.
- **Aggregation:** Calculate average movie ratings and review counts using `AVG`, `COUNT`, and `GROUP BY`.
- **Subqueries and CTEs:** Find highly rated films, users' unwatched watchlist entries, or other multi-step results.
- **Window functions:** Rank movies within a genre or language using functions such as `DENSE_RANK()`.
- **Views:** Provide reusable query definitions for catalogue or rating summaries where appropriate.
- **Indexes:** Add indexes that support measured query patterns, then compare performance with `EXPLAIN` where practical.
- **Transactions:** Keep related changes consistent when a workflow affects multiple records.
- **Integrity constraints:** Demonstrate primary keys, foreign keys, `NOT NULL`, `UNIQUE`, and `CHECK` constraints.
- **Triggers or stored routines:** Add only where they solve a clear requirement and can be explained during evaluation.

The exact set of advanced queries and DBMS features should follow the course rubric. Do not mark an item complete until its SQL and demonstration have been tested.

