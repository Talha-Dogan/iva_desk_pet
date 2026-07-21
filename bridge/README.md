# Bridge — İva'nın araçları (MCP)

İva'nın "iş yapan" tarafı. Bilgisayarında çalışan bir MCP sunucusu; not alma, Telegram,
mod günlüğü, proje takibi ve hatırlatıcı araçlarını yapay zekâya açar.

## Kurulum

```bash
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
```

`.env` dosyasını doldur:

- `MCP_ENDPOINT` — xiaozhi.me → Extensions → MCP Endpoint adresi
- `TELEGRAM_BOT_TOKEN` — @BotFather → `/newbot`
- `TELEGRAM_CHAT_ID` — botu gruba ekle, gruba `/start@botadi` yaz, sonra
  `https://api.telegram.org/bot<TOKEN>/getUpdates` adresinden `"chat":{"id":...}` değerini al

> Bot gizlilik modu açıkken normal grup mesajlarını göremez; bu yüzden grupta `/start@botadi`
> yazman gerekir.

## İki çalışma modu

| Komut | Ne zaman |
|---|---|
| `start_iva_bridge.bat` | Cihaz **resmî sunucuda** (xiaozhi.me) — websocket köprüsü |
| `start_iva_tools_http.bat` | Cihaz **kendi sunucunda** — HTTP (streamable-http) servisi, port 8090 |

Araçların çalışması için ilgili pencerenin açık kalması gerekir.

## Araçlar

**Notlar**

| Araç | Örnek komut |
|---|---|
| `save_note` | "not al: yarın hocaya sor" |
| `read_today_notes` / `read_notes_by_date` | "bugün ne not aldım?" |
| `search_notes` | "notlarımda proje kelimesini ara" |
| `send_notes_to_telegram` / `send_telegram_message` | "notları Telegram'a gönder" |

**Görevler ve odak**

| Araç | Örnek komut |
|---|---|
| `add_task` / `list_tasks` / `complete_task` | "listeye ekle: rapor yaz", "ne yapmam lazım?", "raporu yaptım" |
| `start_pomodoro` | "25 dakika odaklanacağım" — süre bitince Telegram'dan haber |

**Hatırlatıcılar** (diskte kalıcı — PC kapanıp açılsa bile kaybolmaz)

| Araç | Örnek komut |
|---|---|
| `set_reminder` | "20 dakika sonra çayı hatırlat" |
| `set_daily_reminder` | "her gün 9'da ilaç hatırlat" |
| `list_reminders` / `cancel_reminder` | "hatırlatıcılarım", "3 numaralıyı iptal et" |

**Kişisel takip**

| Araç | Örnek komut |
|---|---|
| `log_mood` / `get_mood_history` | "bugün yorgunum" / "bu hafta modum nasıldı?" |
| `add_journal` / `read_journal` | "günlüğüme yaz: ...", "bu hafta neler yazdım?" |
| `track_habit` / `habit_status` | "bugün spor yaptım", "serilerim ne durumda?" |
| `list_projects` / `update_project` | "projelerim ne durumda?" |

**Bilgi ve araçlar**

| Araç | Örnek komut |
|---|---|
| `get_weather` | "İstanbul'da hava nasıl?" (12 Türk şehri, anahtarsız) |
| `calculator`, `get_datetime`, `roll_dice`, `disk_status` | "127 çarpı 43", "saat kaç", "zar at" |

**PC kontrolü**

| Araç | Örnek komut |
|---|---|
| `open_website` | "Google aç", "YouTube aç" (bilinen ~15 site + URL) |
| `play_youtube` | "Tarkan Kuzu Kuzu'yu aç" — yt-dlp ile ilk videoyu bulur, açar, çalar |
| `web_search` | "internette ... ara" — Google araması açar |

PC kontrol araçları `webbrowser.open` kullanır — sadece sayfa açar, komut çalıştırmaz.
`play_youtube` için `yt-dlp`, `open_app` için güvenli bir uygulama listesi kullanılır.

**Spotify tam otomatik çalma** (opsiyonel, Premium gerekir): `play_spotify` varsayılan
olarak Spotify'da aramayı açar. `.env`'e `SPOTIFY_CLIENT_ID`/`SPOTIFY_CLIENT_SECRET`
girip bir kez `python spotify_setup.py` çalıştırırsan, İva şarkıyı **aktif Spotify
cihazında doğrudan çalar** ("Spotify'da X çal"). Anahtarlar: developer.spotify.com/dashboard
→ Create App, Redirect URI `http://127.0.0.1:8888/callback`. Çalma anında Spotify uygulaması
bir cihazda açık olmalıdır.

**PC uygulama açma** (`open_app`): not defteri, hesap makinesi, dosya gezgini, ayarlar,
terminal, Spotify, VS Code, Discord, kamera, takvim gibi bilinen uygulamaları açar —
liste `_KNOWN_APPS` içinde; yenisini eklemek kolaydır. Sadece listedekiler açılır.

Her akşam `DIGEST_HOUR` saatinde günün notları + bekleyen görevler + günlük sorusu
otomatik olarak Telegram'a gönderilir. Veriler günde bir `data/backups/` altına
zip'lenir (son 7 yedek tutulur).

## Dayanıklılık

- **Kalıcı hatırlatıcılar:** diskte (`data/reminders.json`), arka planda bir izleyici
  20 saniyede bir kontrol eder; köprü kapanıp açılsa geçmiş hatırlatıcılar hemen gönderilir
- **Atomik yazma:** JSON dosyaları geçici dosyaya yazılıp yerine taşınır — yazma sırasında
  çökme olsa bile veri bozulmaz
- **Tek örnek kilidi:** aynı anda yalnızca bir köprü çalışır (`bridge.lock`); art arda
  başlatmalar mükerrer bağlantı yaratmaz

## Veriler

`data/` klasöründe tutulur ve **git'e girmez**:

```
data/notes/YYYY-AA-GG.md   günlük notlar
data/mood_log.jsonl        mod kayıtları
data/projects.json         proje durumları
data/state.json            günlük özet takibi
```

## Yeni araç eklemek

`tools.py` içine bir fonksiyon ekle, `@mcp.tool()` ile işaretle. Açıklama satırı önemlidir —
yapay zekâ aracı ne zaman çağıracağını oradan anlar. Türkçe tetikleyici örnekleri yazmak
isabet oranını artırır.

```python
@mcp.tool()
def hava_durumu(sehir: str) -> str:
    """Sehrin hava durumunu soyler. Kullanici 'hava nasil' dediginde cagir."""
    ...
```

## Bilinen sınırlar

- Hatırlatıcılar bellekte tutulur; köprü kapanırsa kaybolur (kalıcı hale getirmek yol haritasında)
- Servisler otomatik başlamaz, PC yeniden başlayınca elle açman gerekir
- Bilgisayar uykuya geçerse araçlar durur
