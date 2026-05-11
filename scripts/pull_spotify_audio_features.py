id="features_script"
import os
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
    scope="",
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
# PULL AUDIO FEATURES
# ---------------------------
rows = []

# Spotify allows batches of 100
for i in range(0, len(track_ids), 100):

    batch = track_ids[i:i+100]

    try:
        features = sp.audio_features(batch)

        for feature in features:

            if feature is None:
                continue

            feature["retrieved_at"] = datetime.now(
                timezone.utc
            ).isoformat()

            rows.append(feature)

        print(f"Processed batch starting at row {i}")

    except Exception as e:
        print(f"FAILED batch {i}: {e}")

# ---------------------------
# BUILD DATAFRAME
# ---------------------------
df = pd.DataFrame(rows)

print(df.head())

# ---------------------------
# LOAD INTO DUCKDB
# ---------------------------
con.register("df", df)

con.execute("""
    CREATE TABLE IF NOT EXISTS raw_spotify_audio_features AS
    SELECT * FROM df LIMIT 0
""")

con.execute("""
    INSERT INTO raw_spotify_audio_features
    SELECT * FROM df
""")

print(f"Loaded rows: {len(df)}")
print("Done ✔")
