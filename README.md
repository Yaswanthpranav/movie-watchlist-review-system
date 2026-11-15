# CineTrack — Movie Watchlist & Community Review Platform

A database-driven web application for discovering movies, managing personal watchlists, and sharing ratings and reviews.

**Project Type:** DBMS Course Project  
**Status:** Implemented  
**Primary Focus:** Relational database design, normalization, integrity constraints, SQL query implementation, and full-stack application development.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Objectives](#objectives)
3. [Implemented Features](#implemented-features)
4. [Team Information and Contributions](#team-information-and-contributions)
5. [Technology Stack](#technology-stack)
6. [System Architecture](#system-architecture)
7. [Database Design](#database-design)
8. [Authentication and Security](#authentication-and-security)
9. [Application Workflows](#application-workflows)
10. [SQL Queries Implemented](#sql-queries-implemented)
11. [Configuration](#configuration)
12. [Running the Application](#running-the-application)

---

## Project Overview

**CineTrack** is a full-stack movie watchlist and community review platform that allows users to explore a movie catalogue, filter movies by language and genre, create personal watchlists, and publish ratings and written reviews.

The project was developed as part of a Database Management Systems (DBMS) course. It demonstrates the practical application of relational database concepts, including schema design, normalization, primary and foreign keys, integrity constraints, joins, aggregate queries, views, and other SQL operations.

The application uses **Supabase PostgreSQL** as its hosted relational database and **Supabase Auth** for user authentication.

---

## Objectives

- Design a relational database with appropriate entities, relationships, and keys.
- Reduce data redundancy through normalization.
- Maintain data consistency using primary keys, foreign keys, `CHECK`, and `UNIQUE` constraints.
- Support movie discovery through title, language, genre, year, and rating-based queries.
- Implement user authentication and profile management.
- Support personal watchlist creation and management.
- Allow users to submit, edit, and delete movie reviews.
- Demonstrate SQL concepts through practical application queries.
- Integrate the database with a full-stack web application.

---

## Implemented Features

- **Movie Catalogue:** Browse available movies and view their details, including release year, duration, language, description, and age rating.
- **Movie Search:** Search for movies by title.
- **Genre Filtering:** Filter movies based on their associated genres.
- **Language Filtering:** Browse movies based on language.
- **Year Filtering:** Retrieve movies based on release year.
- **Streaming Platform Filtering:** Find movies associated with streaming platforms.
- **Movie Details:** View individual movie information and related data.
- **Top-Rated Movies:** Display movies based on their ratings.
- **User Registration and Login:** Authenticate users through Supabase Auth.
- **User Profiles:** Create and retrieve user profile information.
- **Personal Watchlists:** Create multiple named watchlists.
- **Watchlist Management:** Add movies, remove movies, and update their watching status.
- **Community Reviews:** Submit, edit, and delete movie reviews.
- **Rating Summaries:** Calculate and display average movie ratings.
- **Review Timestamps:** Store and retrieve review dates and timestamps.

---

## Team Information and Contributions

| Team Member | Student ID | Responsibilities |
|---|---|---|
| **Mummadi Yasanth Pranav** | `2024A4PS0651H` | Repository setup, Git/GitHub coordination, and README maintenance, backend development |
| **Anisha Potdar** | `2024A3PS2052H` | ER/EER diagram, relational schema, keys, integrity constraints, creation of tables and populating them, database design |
| **Raj Parab** | `2024A3PS0433H` | Requirements analysis, Project integration, backend development, Database Integration & Authentication |
| **Devanshi Patnaik** | `2024A4PS0541H` | Requirements analysis and database blueprint,relational schema, creation of functionality queries, database design |
| **Veer Parekh** | `2024A3PS0430H` | ER/EER diagram and relationship cardinalities, Frontend Implementation, API Development & Application Logic |

---

## Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | React.js, Vite | Interactive user interface |
| Styling | CSS | Layout and visual styling |
| Backend | Python, FastAPI | REST API endpoints and application logic |
| Database | Supabase PostgreSQL | Hosted relational database |
| Authentication | Supabase Auth | User registration and login |
| Configuration | Python environment variables and `.env` | Application configuration |
| Version Control | Git and GitHub | Source control and team collaboration |

---

## System Architecture

CineTrack follows a three-tier application architecture.

```text
┌───────────────────────────────────────────────┐
│                  FRONTEND                     │
│                 React + Vite                  │
│                                               │
│  Movie Catalogue · Search · Watchlists        │
│  Movie Details · Reviews · User Interface     │
└──────────────────────┬────────────────────────┘
                       │
                 HTTP Requests
                    / JSON
                       │
                       ▼
┌───────────────────────────────────────────────┐
│                  BACKEND                      │
│                Python + FastAPI               │
│                                               │
│  API Endpoints · Validation · Business Logic  │
│  CRUD Operations · Authentication Integration│
└──────────────────────┬────────────────────────┘
                       │
                SQLAlchemy / SQL
                       │
                       ▼
┌───────────────────────────────────────────────┐
│                  DATABASE                     │
│             Supabase PostgreSQL               │
│                                               │
│  Tables · Relationships · Constraints · Views │
└───────────────────────────────────────────────┘

             SUPABASE AUTH
       User Registration and Login
```

The React frontend communicates with the FastAPI backend through HTTP requests. The backend handles application logic and performs database operations using SQLAlchemy and Psycopg2.

Supabase PostgreSQL stores the application's relational data, while Supabase Auth manages user authentication.

---

## Database Design

The application database consists of **10 main relational tables**.

| No. | Relation | Purpose |
|---|---|---|
| 1 | `USER` | Stores application user profile information and the linked Supabase Auth user ID. |
| 2 | `WATCHLIST` | Stores named watchlists created by users. |
| 3 | `WATCHLIST_ITEMS` | Stores movies added to individual watchlists, along with their status and added date. |
| 4 | `MOVIE` | Stores movie information such as title, release year, duration, language, description, and age rating. |
| 5 | `LANGUAGE` | Stores the available movie languages. |
| 6 | `GENRE` | Stores the available movie genres. |
| 7 | `MOVIE_GENRE` | Connects movies and genres through a many-to-many relationship. |
| 8 | `REVIEWS` | Stores user ratings and written reviews for movies. |
| 9 | `STREAMING_PLATFORM` | Stores information about streaming platforms. |
| 10 | `MOVIE_PLATFORM` | Connects movies with their associated streaming platforms. |

### Important Relationships

- **USER – WATCHLIST:** One user can create multiple watchlists.
- **WATCHLIST – WATCHLIST_ITEMS:** One watchlist can contain multiple movie entries.
- **MOVIE – WATCHLIST_ITEMS:** A movie can appear in multiple watchlists.
- **MOVIE – GENRE:** A movie can belong to multiple genres, and a genre can be associated with multiple movies. This relationship is implemented through `MOVIE_GENRE`.
- **USER – REVIEWS:** A user can write multiple reviews.
- **MOVIE – REVIEWS:** A movie can have multiple reviews.
- **LANGUAGE – MOVIE:** One language can be associated with multiple movies.
- **MOVIE – STREAMING_PLATFORM:** A movie can be available on multiple streaming platforms. This relationship is implemented through `MOVIE_PLATFORM`.

### Keys and Integrity Constraints

The database uses:

- **Primary Keys (PK):** Uniquely identify records in each relation.
- **Foreign Keys (FK):** Maintain valid relationships between related tables.
- **Composite Primary Keys:** Used in junction tables such as `MOVIE_GENRE` and `MOVIE_PLATFORM`.
- **UNIQUE Constraints:** Prevent duplicate usernames, emails, genre names, language names, and other specified duplicate values.
- **CHECK Constraints:** Ensure that movie review ratings remain between 1 and 5.
- **Referential Integrity:** Ensures that related records reference valid parent records.

---

## Authentication and Security

CineTrack uses **Supabase Auth** for user registration and login.

- User credentials are managed by Supabase Auth rather than being stored directly in the application database.
- The application `USER` table contains an `auth_user_id` column linked to `auth.users(id)`.
- A database trigger synchronizes newly registered Supabase Auth users with the application user profile table.
- Row Level Security (RLS) policies are enabled on the application tables.
- Users can access and modify their own profile and personal watchlist data according to the configured policies.
- Review access is controlled through the configured database policies.

Sensitive configuration values, including database passwords and Supabase secret keys, are stored in environment variables and must not be committed to the GitHub repository.

---

## Application Workflows

### 1. Movie Discovery and Search

1. A user opens the movie catalogue.
2. The user can search by title or filter movies by genre, language, release year, or streaming platform.
3. The frontend sends the selected criteria to the FastAPI backend.
4. The backend executes the relevant SQL queries against Supabase PostgreSQL.
5. Matching movies and their associated details are returned to the frontend.

### 2. Watchlist Management

1. An authenticated user creates a named watchlist.
2. The watchlist is associated with the user's profile.
3. The user adds movies from the catalogue to the watchlist.
4. The user can view the movies saved in the watchlist.
5. The user can update the status of a movie or remove it from the watchlist.

### 3. Review Publishing

1. An authenticated user selects a movie.
2. The user submits a rating between 1 and 5 and optional written feedback.
3. The backend validates the submitted information.
4. The review is stored in the `REVIEWS` table.
5. Users can edit or delete their own reviews.
6. Average ratings are calculated and displayed using the implemented database queries and view.

---

## SQL Queries Implemented

The project includes 22 SQL query scripts demonstrating different database operations and application workflows.

| No. | Query | Description |
|---|---|---|
| 01 | Display All Movies | Retrieves all movies from the catalogue. |
| 02 | Search Movies by Title | Searches for movies using their titles. |
| 03 | Genre Dropdown | Retrieves genre information for filtering. |
| 04 | Streaming Platform Dropdown | Retrieves streaming platform information for filtering. |
| 05 | Rating Handling | Handles movie rating-related operations. |
| 06 | Year | Retrieves or filters movies based on release year. |
| 07 | Combined Displaying Query | Combines multiple movie-related filters or details. |
| 08 | Top-Rated Page | Retrieves top-rated movies. |
| 09 | Movie Details | Retrieves detailed information about a selected movie. |
| 10 | Retrieve User Profile | Retrieves a user's profile information. |
| 11 | Create User Profile | Creates a user profile. |
| 12 | Retrieve User Watchlists | Retrieves watchlists associated with a user. |
| 13 | Display Movies in Watchlist | Displays movies belonging to a selected watchlist. |
| 14 | Add to Watchlist | Adds a movie to a watchlist. |
| 15 | Remove from Watchlist | Removes a movie from a watchlist. |
| 16 | Update Status | Updates the status of a watchlist item. |
| 17 | Create Watchlist | Creates a new named watchlist. |
| 18 | Submit Review | Inserts a new movie review. |
| 19 | Edit Review | Updates an existing review. |
| 20 | Delete Review | Deletes a review. |
| 21 | Average Ratings View | Uses a database view to retrieve average movie ratings. |
| 22 | Review Timestamp | Retrieves or handles review timestamp information. |

These queries demonstrate catalogue retrieval, filtering, joins, CRUD operations, aggregation, and database views.

---

## Configuration

The backend uses a `.env` file to store environment-specific configuration.

Create a `.env` file inside the `backend` directory.

Example configuration:

```env
DATABASE_URL=your_supabase_postgresql_connection_string

SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_or_publishable_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_secret_or_service_role_key

SECRET_KEY=your_long_random_secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
---

## Running the Application

### Prerequisites

- Python installed
- Node.js and npm installed
- Access to the CineTrack Supabase project
- Git installed

### 1. Clone the Repository

```bash
git clone <repository-url>
cd movie-watchlist-review-system
```

### 2. Start the Backend

Open a terminal and navigate to the backend directory:

```bash
cd backend
```

Configure the `.env` file with the required Supabase credentials and database connection string.

Start the FastAPI server:

```bash
python -m uvicorn app.main:app --reload
```

The backend will be available at:

```text
http://127.0.0.1:8000
```

FastAPI interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

### 3. Start the Frontend

Open a separate terminal and navigate to the frontend directory:

```bash
cd frontend
```

Install the frontend dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

On Windows PowerShell, if the npm script execution policy blocks `npm`, use:

```powershell
npm.cmd install
npm.cmd run dev
```

The frontend will generally be available at:

```text
http://localhost:5173
```

### 4. Access the Application

Open the frontend URL in a browser, register or log in using Supabase Auth, and explore the CineTrack application.

---

## Conclusion

CineTrack demonstrates the integration of relational database concepts into a practical full-stack web application. By combining React, FastAPI, Supabase PostgreSQL, and Supabase Auth, the project provides movie discovery, personal watchlist management, and community review functionality while demonstrating database design, integrity constraints, SQL queries, and authentication.

