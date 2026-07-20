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

| Araç | Örnek komut |
|---|---|
| `save_note` | "not al: yarın hocaya sor" |
| `read_today_notes` / `read_notes_by_date` | "bugün ne not aldım?" |
| `search_notes` | "notlarımda proje kelimesini ara" |
| `send_notes_to_telegram` | "notları Telegram'a gönder" |
| `send_telegram_message` | "Telegram'a yaz: geldim" |
| `log_mood` / `get_mood_history` | "bugün yorgunum" / "bu hafta modum nasıldı?" |
| `list_projects` / `update_project` | "projelerim ne durumda?" |
| `set_reminder` | "20 dakika sonra hatırlat" |
| `calculator`, `get_datetime`, `roll_dice`, `disk_status` | "127 çarpı 43", "saat kaç", "zar at" |

Ayrıca her akşam `DIGEST_HOUR` saatinde günün notları otomatik olarak Telegram'a gönderilir.

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
