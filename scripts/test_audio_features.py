import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

# ---------------------------
# AUTH (USER CONTEXT)
# ---------------------------
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
    scope=""  # not required for audio_features, but keeps flow simple
))

# ---------------------------
# TEST TRACK
# ---------------------------
track_id = "3n3Ppam7vgaVa1iaRUc9Lp"

# ---------------------------
# CALL API
# ---------------------------
try:
    result = sp.audio_features([track_id])
    print("SUCCESS ✔")
    print(result)

except Exception as e:
    print("FAILED ❌")
    print(str(e))