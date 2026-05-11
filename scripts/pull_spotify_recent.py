import os
from dotenv import load_dotenv
from datetime import datetime, timezone

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import duckdb
import pandas as pd

# Load environment variables
load_dotenv()

# ---------------------------
# AUTH
# ---------------------------
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    scope="user-read-recently-played",
    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET")
))

# ---------------------------
# PULL DATA (PAGINATED)
# ---------------------------

all_rows = []
before = None
target_rows = 500

while len(all_rows) < target_rows:

    results = sp.current_user_recently_played(
        limit=50,
        before=before
    )

    items = results["items"]

    # Stop if Spotify returns nothing
    if not items:
        break

    for item in items:
        track = item["track"]

        all_rows.append({
            "played_at": item["played_at"],
            "track_id": track["id"],
            "track_name": track["name"],
            "artist_name": track["artists"][0]["name"],
            "album_name": track["album"]["name"],
            "duration_ms": track["duration_ms"],
            "retrieved_at": datetime.now(timezone.utc).isoformat()
        })

    # Grab oldest played_at timestamp
    oldest_played_at = items[-1]["played_at"]

    # Convert to Unix milliseconds
    before = int(
        pd.Timestamp(oldest_played_at).timestamp() * 1000
    )

    print(f"Pulled {len(all_rows)} tracks so far...")

# Build dataframe
df = pd.DataFrame(all_rows)

# Remove duplicates
df = df.drop_duplicates(subset=["played_at", "track_id"])

# ---------------------------
# LOAD INTO DUCKDB
# ---------------------------
con = duckdb.connect("dev.duckdb")

con.register("df", df)

con.execute("""
    CREATE TABLE IF NOT EXISTS raw_spotify_recent_tracks AS
    SELECT * FROM df LIMIT 0
""")

con.execute("""
    INSERT INTO raw_spotify_recent_tracks
    SELECT * FROM df
""")

print(f"Loaded rows: {len(df)}")
print("Done ✔")