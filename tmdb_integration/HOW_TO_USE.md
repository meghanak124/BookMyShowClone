# TMDB Auto-Fetch Setup

## Step 1 — Get a free TMDB API Key
1. Go to https://www.themoviedb.org/settings/api
2. Sign up (free) → click "Create" → choose "Developer"
3. Copy your **API Key (v3 auth)**

## Step 2 — Add the key to your .env
Open your `.env` file and add:
```
TMDB_API_KEY=paste_your_key_here
```
(Keep all your existing Cloudinary and SECRET_KEY values as they are)

## Step 3 — Copy these files into your project
Copy the `movies/` folder from this zip into your project root.
It only adds new files — nothing existing is modified.

```
Your project/
└── movies/
    └── management/          ← NEW FOLDER
        ├── __init__.py
        └── commands/
            ├── __init__.py
            └── fetch_movies.py   ← THE COMMAND
```

## Step 4 — Run the command

```bash
# Fetch Now Playing movies (default, 2 pages = ~40 movies)
python manage.py fetch_movies

# Fetch popular movies, 3 pages
python manage.py fetch_movies --type popular --pages 3

# Fetch upcoming movies
python manage.py fetch_movies --type upcoming

# Fetch only Hindi movies
python manage.py fetch_movies --language hi

# Fetch only Tamil movies
python manage.py fetch_movies --language ta

# Combine: popular Telugu movies, 1 page
python manage.py fetch_movies --type popular --language te --pages 1
```

## What it does
- Fetches movie title, genre, description, language, release date, runtime, rating
- Downloads poster from TMDB and uploads it to YOUR Cloudinary account
- Skips movies already in your DB (by title) — safe to run multiple times
- All other features (shows, bookings, reviews, admin) work exactly as before

## Notes
- Theatres and Shows are NOT auto-created — you still add those in Django Admin
  (because show timings and seat configs are specific to your setup)
- You can still manually add/edit movies in Django Admin as usual
- Re-running the command won't create duplicates
