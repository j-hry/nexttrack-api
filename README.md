# NextTrack

A stateless RESTful music recommendation API that generates personalised track recommendations from a short listening history, without storing any user data.

Built with FastAPI and PostgreSQL, using Last.fm as the external data source.

## Features

- Single `POST /api/v1/recommend` endpoint
- Five user-controllable parameters: diversity, popularity, tags, tag match type, exclude same artist
- Hybrid recommendation approach: Last.fm collaborative similarity for candidate generation, content-based re-ranking via user parameters
- Global API response caching with PostgreSQL (no user-specific data stored)
- Transparent explanations for each recommendation

**Live demo:** https://nexttrack-api.onrender.com/

## Tech Stack

- **Backend:** FastAPI, PostgreSQL, psycopg2, Pydantic
- **Frontend:** Vanilla JavaScript, HTML5, CSS3
- **External API:** Last.fm
- **Testing:** pytest

## Prerequisites

- Python 3.10+
- PostgreSQL
- A [Last.fm API key](https://www.last.fm/api/account/create)

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/j-hry/nexttrack-api.git
cd nexttrack-api
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Set up PostgreSQL

Create a database, then run the following SQL to create the cache tables:

```sql
CREATE TABLE similar_tracks_cache (
    artist TEXT NOT NULL,
    track TEXT NOT NULL,
    similar_tracks JSONB NOT NULL,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (artist, track)
);

CREATE TABLE artist_tags_cache (
    artist TEXT NOT NULL PRIMARY KEY,
    tags JSONB NOT NULL,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE track_tags_cache (
    artist TEXT NOT NULL,
    track TEXT NOT NULL,
    tags JSONB NOT NULL,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (artist, track)
);
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```
LASTFM_API_KEY=your_api_key_here
DATABASE_URL=postgresql://username:password@localhost:5432/your_database_name
```

### 5. Run the server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. API documentation is at `http://localhost:8000/docs`.

### 6. Open the frontend

Navigate to `http://localhost:8000` in your browser.

## Running Tests

```bash
pytest tests/
```