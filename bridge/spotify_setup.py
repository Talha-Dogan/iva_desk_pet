"""Spotify tam-otomatik calma icin BIR KERELIK yetkilendirme (Premium gerekir).

Kullanim:
    1. .env'e SPOTIFY_CLIENT_ID ve SPOTIFY_CLIENT_SECRET gir
       (https://developer.spotify.com/dashboard -> Create App;
        Redirect URI: http://127.0.0.1:8888/callback).
    2. Bu betigi terminalde calistir:  venv\\Scripts\\python.exe spotify_setup.py
    3. Ekrandaki linki tarayicida ac, Spotify'da "izin ver" de.
    4. Yonlendigin (127.0.0.1:8888/callback?code=...) adresi kopyalayip yapistir.
    Token data/.spotify_cache'e kaydedilir; bir daha izin istenmez.
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(BASE_DIR, "data", ".spotify_cache")
REDIRECT = "http://127.0.0.1:8888/callback"
SCOPE = "user-modify-playback-state user-read-playback-state"


def load_env():
    p = os.path.join(BASE_DIR, ".env")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())


def main():
    load_env()
    cid = os.environ.get("SPOTIFY_CLIENT_ID", "").strip()
    secret = os.environ.get("SPOTIFY_CLIENT_SECRET", "").strip()
    if not cid or not secret:
        print("HATA: once .env'e SPOTIFY_CLIENT_ID ve SPOTIFY_CLIENT_SECRET gir.")
        return

    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    from spotipy.oauth2 import SpotifyOAuth
    auth = SpotifyOAuth(client_id=cid, client_secret=secret,
                        redirect_uri=REDIRECT, scope=SCOPE,
                        cache_path=CACHE, open_browser=False)

    print("\n1) Bu linki tarayicida ac ve Spotify'da 'izin ver' de:\n")
    print("   " + auth.get_authorize_url() + "\n")
    print("2) Yonlendigin adres (127.0.0.1:8888/callback?code=...) acilmayacak,")
    print("   sorun degil. Adres cubugundaki TAM URL'yi kopyala.\n")
    resp = input("Yonlendigin URL'yi buraya yapistir: ").strip()

    code = auth.parse_response_code(resp)
    auth.get_access_token(code, as_dict=False)
    print("\nBASARILI! Token kaydedildi:", CACHE)
    print("Artik Iva'ya 'spotify'da X cal' diyebilirsin (Spotify acikken).")


if __name__ == "__main__":
    main()
