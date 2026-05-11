id="analysis_script"
import os
import json
from dotenv import load_dotenv
from datetime import datetime, timezone

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import duckdb
import pandas as pd

# ---------------------------
# LOAD ENV VARS
# ---------------------------
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
# CONNECT TO DUCKDB
# ---------------------------
con = duckdb.connect("dev.duckdb")

# ---------------------------
# GET TRACK IDS
# ---------------------------
track_df = con.execute("""
    SELECT DISTINCT track_id
    FROM raw_spotify_recent_tracks
    WHERE track_id IS NOT NULL
""").fetchdf()

track_ids = track_df["track_id"].tolist()

print(f"Found {len(track_ids)} track_ids")

# ---------------------------
# PULL AUDIO ANALYSIS
# ---------------------------
rows = []

for i, track_id in enumerate(track_ids):

    try:
        analysis = sp.audio_analysis(track_id)

        rows.append({
            "track_id": track_id,
            "analysis_json": json.dumps(analysis),
            "retrieved_at": datetime.now(timezone.utc).isoformat()
        })

        print(f"[{i+1}/{len(track_ids)}] Pulled analysis for {track_id}")

    except Exception as e:
        print(f"FAILED for {track_id}: {e}")

# ---------------------------
# BUILD DATAFRAME
# ---------------------------
df = pd.DataFrame(rows)

# ---------------------------
# LOAD INTO DUCKDB
# ---------------------------
con.register("df", df)

con.execute("""
    CREATE TABLE IF NOT EXISTS raw_spotify_audio_analysis AS
    SELECT * FROM df LIMIT 0
""")

con.execute("""
    INSERT INTO raw_spotify_audio_analysis
    SELECT * FROM df
""")

print(f"Loaded rows: {len(df)}")
print("Done ✔")
