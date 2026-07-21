"""
Iva'nin yerel araclari (MCP stdio sunucusu) - Faz 1: Sekreter Iva

Yetenekler:
- Not alma / okuma / arama (data/notes/*.md)
- Telegram'a mesaj ve gunluk not ozeti gonderme
- Mod (ruh hali) gunlugu ve gecmisi
- Proje hafizasi (data/projects.json)
- Hatirlatici (Telegram uzerinden)
- Hesap makinesi, saat, zar, disk durumu

Telegram icin .env dosyasina TELEGRAM_BOT_TOKEN ve TELEGRAM_CHAT_ID eklenmeli.
"""
import ast
import datetime
import json
import operator
import os
import random
import shutil
import threading
import urllib.parse
import urllib.request

from mcp.server.fastmcp import FastMCP

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
NOTES_DIR = os.path.join(DATA_DIR, "notes")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
MOOD_FILE = os.path.join(DATA_DIR, "mood_log.jsonl")
PROJECTS_FILE = os.path.join(DATA_DIR, "projects.json")
STATE_FILE = os.path.join(DATA_DIR, "state.json")
REMINDERS_FILE = os.path.join(DATA_DIR, "reminders.json")
TASKS_FILE = os.path.join(DATA_DIR, "tasks.json")
HABITS_FILE = os.path.join(DATA_DIR, "habits.json")
JOURNAL_FILE = os.path.join(DATA_DIR, "journal.jsonl")

os.makedirs(NOTES_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# Tum dosya yazimlarini seri hale getiren tek kilit (es zamanli arac cagrilari
# ayni dosyayi bozmasin diye).
_file_lock = threading.RLock()


def _load_env():
    env_path = os.path.join(BASE_DIR, ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())


_load_env()

mcp = FastMCP("IvaTools")

# ---------------------------------------------------------------- helpers

DAYS_TR = ["Pazartesi", "Sali", "Carsamba", "Persembe", "Cuma", "Cumartesi", "Pazar"]


def _now():
    return datetime.datetime.now()


def _today_str():
    return _now().strftime("%Y-%m-%d")


def _note_path(date_str):
    return os.path.join(NOTES_DIR, f"{date_str}.md")


def _telegram_config():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    return token, chat_id


def _telegram_send(text):
    token, chat_id = _telegram_config()
    if not token or not chat_id:
        return False, "Telegram ayarli degil (.env dosyasina TELEGRAM_BOT_TOKEN ve TELEGRAM_CHAT_ID ekle)."
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
        req = urllib.request.Request(
            url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            ok = resp.status == 200
        return ok, "gonderildi" if ok else f"HTTP {resp.status}"
    except Exception as exc:
        return False, f"Telegram hatasi: {exc}"


def _read_notes(date_str):
    path = _note_path(date_str)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return f.read().strip()


def _load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _save_json(path, data):
    # Atomik yazim: once benzersiz bir .tmp'ye yaz, sonra yerine tasi. Yazma
    # sirasinda cokme olsa bile asil dosya bozulmaz. Gecici ad sirece ozgu
    # (pid) ki ayni klasoru kullanan iki sirec ayni tmp'de cakismasin.
    with _file_lock:
        tmp = f"{path}.{os.getpid()}.tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except OSError:
                    pass


def _append_jsonl(path, entry):
    with _file_lock:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------- notes

@mcp.tool()
def save_note(text: str, category: str = "genel") -> str:
    """Kullanicinin notunu kaydeder. Saves a note for the user.
    Kullanici 'not al', 'bunu kaydet', 'unutmayayim' gibi seyler dediginde cagir.
    category: ders, toplanti, fikir, yapilacak veya genel olabilir."""
    now = _now()
    path = _note_path(_today_str())
    with _file_lock:
        is_new = not os.path.exists(path)
        with open(path, "a", encoding="utf-8") as f:
            if is_new:
                f.write(f"# {_today_str()} {DAYS_TR[now.weekday()]}\n\n")
            f.write(f"- [{now.strftime('%H:%M')}] ({category}) {text}\n")
    return f"Not kaydedildi ({category})."


@mcp.tool()
def read_today_notes() -> str:
    """Bugunun notlarini okur. Reads today's notes.
    Kullanici 'bugun ne not aldim', 'notlarimi oku' dediginde cagir."""
    content = _read_notes(_today_str())
    if not content:
        return "Bugun icin kayitli not yok."
    return content


@mcp.tool()
def read_notes_by_date(date: str) -> str:
    """Belirli bir gunun notlarini okur. Reads notes for a date (YYYY-MM-DD)."""
    content = _read_notes(date)
    if not content:
        return f"{date} icin kayitli not yok."
    return content


@mcp.tool()
def search_notes(query: str) -> str:
    """Tum notlarda arama yapar. Searches all saved notes for a keyword."""
    query_l = query.lower()
    hits = []
    for name in sorted(os.listdir(NOTES_DIR), reverse=True):
        if not name.endswith(".md"):
            continue
        with open(os.path.join(NOTES_DIR, name), encoding="utf-8") as f:
            for line in f:
                if query_l in line.lower():
                    hits.append(f"{name[:-3]}: {line.strip()}")
        if len(hits) >= 15:
            break
    if not hits:
        return f"'{query}' ile eslesen not bulunamadi."
    return "\n".join(hits[:15])


@mcp.tool()
def send_notes_to_telegram(date: str = "") -> str:
    """Gunun notlarini Telegram grubuna gonderir. Sends the day's notes to Telegram.
    Kullanici 'notlari telegrama at/gonder' dediginde cagir. date bos ise bugun."""
    date_str = date.strip() or _today_str()
    content = _read_notes(date_str)
    if not content:
        return f"{date_str} icin gonderilecek not yok."
    ok, msg = _telegram_send(f"Iva - {date_str} notlari:\n\n{content}")
    return "Notlar Telegram'a gonderildi." if ok else msg


@mcp.tool()
def send_telegram_message(text: str) -> str:
    """Telegram grubuna serbest mesaj gonderir. Sends a message to the Telegram group.
    Kullanici 'telegrama yaz/gonder: ...' dediginde cagir."""
    ok, msg = _telegram_send(text)
    return "Mesaj Telegram'a gonderildi." if ok else msg


# ---------------------------------------------------------------- mood

@mcp.tool()
def log_mood(mood: str, score: int = 0, note: str = "") -> str:
    """Kullanicinin gunluk ruh halini kaydeder. Logs the user's mood.
    Kullanici moduyla ilgili bir sey soylediginde (yorgunum, harikayim vb.) cagir.
    mood: kisa ozet (mutlu, yorgun, stresli...). score: 1-10 arasi (bilinmiyorsa 0)."""
    entry = {
        "time": _now().strftime("%Y-%m-%d %H:%M"),
        "mood": mood,
        "score": max(0, min(int(score), 10)),
        "note": note,
    }
    _append_jsonl(MOOD_FILE, entry)
    return "Mod kaydedildi."


@mcp.tool()
def get_mood_history(days: int = 7) -> str:
    """Son gunlerin mod kayitlarini getirir. Returns mood history for the last N days."""
    if not os.path.exists(MOOD_FILE):
        return "Henuz mod kaydi yok."
    cutoff = _now() - datetime.timedelta(days=max(1, days))
    lines = []
    with open(MOOD_FILE, encoding="utf-8") as f:
        for raw in f:
            try:
                e = json.loads(raw)
                t = datetime.datetime.strptime(e["time"], "%Y-%m-%d %H:%M")
                if t >= cutoff:
                    score = f" ({e['score']}/10)" if e.get("score") else ""
                    note = f" - {e['note']}" if e.get("note") else ""
                    lines.append(f"{e['time']}: {e['mood']}{score}{note}")
            except Exception:
                continue
    if not lines:
        return f"Son {days} gunde mod kaydi yok."
    return "\n".join(lines[-30:])


# ---------------------------------------------------------------- projects

@mcp.tool()
def list_projects() -> str:
    """Kullanicinin projelerini ve durumlarini listeler. Lists the user's projects.
    Kullanici projelerini sordugunda veya sen sohbette proje sormak istediginde cagir."""
    projects = _load_json(PROJECTS_FILE, {})
    if not projects:
        return "Kayitli proje yok. update_project araciyla proje eklenebilir."
    lines = []
    for name, info in projects.items():
        lines.append(f"- {name}: {info.get('status', '?')} (guncelleme: {info.get('updated', '?')})")
    return "\n".join(lines)


@mcp.tool()
def update_project(name: str, status: str) -> str:
    """Bir projenin durumunu kaydeder/gunceller. Creates or updates a project's status.
    Kullanici bir projesinden bahsedip ilerleme anlattiginda cagir."""
    projects = _load_json(PROJECTS_FILE, {})
    projects[name] = {"status": status, "updated": _today_str()}
    _save_json(PROJECTS_FILE, projects)
    return f"'{name}' projesi guncellendi."


# ---------------------------------------------------------------- reminders
#
# Hatirlaticilar DISKTE tutulur (data/reminders.json). Kopru kapanip acilsa bile
# kaybolmaz: acilista yeniden yuklenir, gecmis olanlar hemen gonderilir.
# Arka planda bir izleyici her 20 saniyede bir suresi gelenleri tetikler.

_reminders_lock = threading.RLock()


def _load_reminders():
    return _load_json(REMINDERS_FILE, [])


def _save_reminders(items):
    _save_json(REMINDERS_FILE, items)


def _fire_reminder(rem):
    ok, _ = _telegram_send(f"⏰ Hatirlatma: {rem['message']}")
    return ok


def _reminder_loop():
    while True:
        try:
            now_ts = _now().timestamp()
            with _reminders_lock:
                items = _load_reminders()
                remaining = []
                changed = False
                for rem in items:
                    if rem.get("done"):
                        continue
                    if rem["due_ts"] <= now_ts:
                        if _fire_reminder(rem):
                            changed = True
                            if rem.get("repeat_hours"):
                                rem["due_ts"] += rem["repeat_hours"] * 3600
                                remaining.append(rem)
                            # tek seferlikler dusuyor
                        else:
                            remaining.append(rem)  # gonderilemedi, tekrar dene
                    else:
                        remaining.append(rem)
                if changed:
                    _save_reminders(remaining)
        except Exception:
            pass
        threading.Event().wait(20)


@mcp.tool()
def set_reminder(minutes: int, message: str) -> str:
    """Belirtilen dakika sonra Telegram'dan hatirlatma gonderir. Sets a one-off reminder.
    Kullanici 'X dakika/saat sonra hatirlat' dediginde cagir. minutes: kac dakika sonra.
    Hatirlaticilar diskte tutulur; bilgisayar kapanip acilsa bile kaybolmaz."""
    token, chat_id = _telegram_config()
    if not token or not chat_id:
        return "Hatirlatici icin once Telegram ayarlanmali (.env)."
    minutes = max(1, min(int(minutes), 60 * 24 * 30))
    due = _now() + datetime.timedelta(minutes=minutes)
    with _reminders_lock:
        items = _load_reminders()
        items.append({
            "id": int(_now().timestamp() * 1000) % 1000000,
            "message": message,
            "due_ts": due.timestamp(),
            "due_human": due.strftime("%d.%m %H:%M"),
            "repeat_hours": 0,
            "done": False,
        })
        _save_reminders(items)
    return f"Tamam, {due.strftime('%d.%m %H:%M')} icin hatirlatici kurdum."


@mcp.tool()
def set_daily_reminder(hour: int, minute: int, message: str) -> str:
    """Her gun ayni saatte tekrarlayan hatirlatma kurar. Sets a daily repeating reminder.
    Kullanici 'her gun saat X'te hatirlat' dediginde cagir."""
    token, chat_id = _telegram_config()
    if not token or not chat_id:
        return "Hatirlatici icin once Telegram ayarlanmali (.env)."
    hour = max(0, min(int(hour), 23))
    minute = max(0, min(int(minute), 59))
    now = _now()
    due = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if due <= now:
        due += datetime.timedelta(days=1)
    with _reminders_lock:
        items = _load_reminders()
        items.append({
            "id": int(_now().timestamp() * 1000) % 1000000,
            "message": message,
            "due_ts": due.timestamp(),
            "due_human": f"her gun {hour:02d}:{minute:02d}",
            "repeat_hours": 24,
            "done": False,
        })
        _save_reminders(items)
    return f"Her gun {hour:02d}:{minute:02d} icin hatirlatici kurdum."


@mcp.tool()
def list_reminders() -> str:
    """Bekleyen hatirlaticilari listeler. Lists pending reminders."""
    with _reminders_lock:
        items = [r for r in _load_reminders() if not r.get("done")]
    if not items:
        return "Bekleyen hatirlatici yok."
    items.sort(key=lambda r: r["due_ts"])
    lines = []
    for r in items:
        tekrar = " (her gun)" if r.get("repeat_hours") == 24 else ""
        lines.append(f"#{r['id']} - {r['due_human']}{tekrar}: {r['message']}")
    return "\n".join(lines)


@mcp.tool()
def cancel_reminder(reminder_id: int) -> str:
    """Bir hatirlaticiyi iptal eder. Cancels a reminder by its id.
    Once list_reminders ile id'yi ogren."""
    with _reminders_lock:
        items = _load_reminders()
        before = len(items)
        items = [r for r in items if r.get("id") != int(reminder_id)]
        _save_reminders(items)
    if len(items) < before:
        return f"#{reminder_id} numarali hatirlatici iptal edildi."
    return f"#{reminder_id} numarali hatirlatici bulunamadi."


# ---------------------------------------------------------------- tasks (yapilacaklar)
#
# Notlardan farkli: gorevler tamamlanabilir ve listede kalir.

@mcp.tool()
def add_task(text: str) -> str:
    """Yapilacaklar listesine gorev ekler. Adds a to-do task.
    Kullanici 'sunu yapmam lazim', 'listeye ekle', 'yapilacaklara ekle' dediginde cagir."""
    with _file_lock:
        tasks = _load_json(TASKS_FILE, [])
        tasks.append({
            "id": (max([t["id"] for t in tasks], default=0) + 1),
            "text": text,
            "done": False,
            "created": _today_str(),
        })
        _save_json(TASKS_FILE, tasks)
    return f"Gorev eklendi: {text}"


@mcp.tool()
def list_tasks(show_done: bool = False) -> str:
    """Yapilacaklar listesini gosterir. Lists to-do tasks.
    Kullanici 'ne yapmam lazim', 'listemde ne var', 'gorevlerim' dediginde cagir."""
    tasks = _load_json(TASKS_FILE, [])
    if not show_done:
        tasks = [t for t in tasks if not t.get("done")]
    if not tasks:
        return "Listede gorev yok." if not show_done else "Hic gorev yok."
    lines = []
    for t in tasks:
        mark = "[x]" if t.get("done") else "[ ]"
        lines.append(f"{mark} #{t['id']} {t['text']}")
    return "\n".join(lines)


@mcp.tool()
def complete_task(task_id: int) -> str:
    """Bir gorevi tamamlandi olarak isaretler. Marks a task done.
    Kullanici 'sunu yaptim', 'X gorevini tamamladim' dediginde cagir."""
    with _file_lock:
        tasks = _load_json(TASKS_FILE, [])
        for t in tasks:
            if t["id"] == int(task_id):
                t["done"] = True
                t["completed"] = _today_str()
                _save_json(TASKS_FILE, tasks)
                return f"Tebrikler! '{t['text']}' tamamlandi."
    return f"#{task_id} numarali gorev bulunamadi."


# ---------------------------------------------------------------- pomodoro (odak)
#
# Odak seansi: sure boyunca calis, bitince Telegram'dan haber ver.
# Firmware'e dokunmadan; sadece bildirim tarafi.

@mcp.tool()
def start_pomodoro(minutes: int = 25, task: str = "") -> str:
    """Odak (pomodoro) seansi baslatir; sure bitince Telegram'dan haber gelir.
    Starts a focus session. Kullanici 'odaklanacagim', 'pomodoro baslat',
    'X dakika calisacagim' dediginde cagir. Varsayilan 25 dakika."""
    token, chat_id = _telegram_config()
    minutes = max(1, min(int(minutes), 180))
    label = f" ({task})" if task else ""
    due = _now() + datetime.timedelta(minutes=minutes)
    if token and chat_id:
        with _reminders_lock:
            items = _load_reminders()
            items.append({
                "id": int(_now().timestamp() * 1000) % 1000000,
                "message": f"Odak seansi bitti{label}! {minutes} dakika calistin, mola ver.",
                "due_ts": due.timestamp(),
                "due_human": due.strftime("%H:%M"),
                "repeat_hours": 0,
                "done": False,
            })
            _save_reminders(items)
    return (f"{minutes} dakikalik odak seansi basladi{label}. "
            f"Bitince ({due.strftime('%H:%M')}) haber verecegim. Basarilar!")


# ---------------------------------------------------------------- journal (gunluk)
#
# Mod'dan farkli: serbest gunluk yazisi. Aksam bir cumle sorup kaydeder.

@mcp.tool()
def add_journal(text: str) -> str:
    """Gunluk defterine bir yazi ekler. Adds a journal entry.
    Kullanici gununu anlatinca, 'gunlugume yaz', 'bugun sunlar oldu' dediginde cagir."""
    _append_jsonl(JOURNAL_FILE, {
        "time": _now().strftime("%Y-%m-%d %H:%M"),
        "text": text,
    })
    return "Gunlugune yazdim."


@mcp.tool()
def read_journal(days: int = 7) -> str:
    """Son gunlerin gunluk yazilarini getirir. Reads recent journal entries."""
    if not os.path.exists(JOURNAL_FILE):
        return "Henuz gunluk yazisi yok."
    cutoff = _now() - datetime.timedelta(days=max(1, days))
    lines = []
    with open(JOURNAL_FILE, encoding="utf-8") as f:
        for raw in f:
            try:
                e = json.loads(raw)
                t = datetime.datetime.strptime(e["time"], "%Y-%m-%d %H:%M")
                if t >= cutoff:
                    lines.append(f"{e['time']}: {e['text']}")
            except Exception:
                continue
    return "\n".join(lines[-30:]) if lines else f"Son {days} gunde gunluk yazisi yok."


# ---------------------------------------------------------------- habits (aliskanlik)

@mcp.tool()
def track_habit(name: str) -> str:
    """Bir aliskanligi bugun icin isaretler. Marks a habit done for today.
    Kullanici 'bugun spor yaptim', 'kitap okudum', 'su ictim' gibi tekrarli
    seyler soyleyince cagir. name: aliskanligin kisa adi (spor, kitap, su...)."""
    name = name.strip().lower()
    today = _today_str()
    with _file_lock:
        habits = _load_json(HABITS_FILE, {})
        days = habits.get(name, [])
        if today in days:
            return f"'{name}' bugun zaten isaretli. Aferin, seri devam ediyor!"
        days.append(today)
        habits[name] = days
        _save_json(HABITS_FILE, habits)
    streak = _habit_streak(days)
    return f"'{name}' isaretlendi. {streak} gunluk seri!"


def _habit_streak(days):
    if not days:
        return 0
    dset = set(days)
    streak = 0
    d = _now().date()
    while d.strftime("%Y-%m-%d") in dset:
        streak += 1
        d -= datetime.timedelta(days=1)
    return streak


@mcp.tool()
def habit_status(name: str = "") -> str:
    """Aliskanlik durumunu/serisini gosterir. Shows habit streaks.
    name bos ise tum aliskanliklari listeler."""
    habits = _load_json(HABITS_FILE, {})
    if not habits:
        return "Henuz takip edilen aliskanlik yok."
    if name:
        name = name.strip().lower()
        if name not in habits:
            return f"'{name}' diye bir aliskanlik takip edilmiyor."
        return f"'{name}': {_habit_streak(habits[name])} gunluk seri, toplam {len(habits[name])} gun."
    lines = []
    for h, days in habits.items():
        lines.append(f"- {h}: {_habit_streak(days)} gunluk seri (toplam {len(days)} gun)")
    return "\n".join(lines)


# ---------------------------------------------------------------- weather (hava durumu)

_TR_CITIES = {
    "istanbul": (41.01, 28.98), "ankara": (39.93, 32.85), "izmir": (38.42, 27.14),
    "bursa": (40.19, 29.06), "antalya": (36.90, 30.70), "adana": (37.00, 35.32),
    "konya": (37.87, 32.48), "gaziantep": (37.07, 37.38), "kayseri": (38.73, 35.48),
    "eskisehir": (39.78, 30.52), "trabzon": (41.00, 39.72), "samsun": (41.29, 36.33),
}
_WMO = {
    0: "acik", 1: "az bulutlu", 2: "parcali bulutlu", 3: "cok bulutlu",
    45: "sisli", 48: "sisli", 51: "cisenti", 53: "cisenti", 55: "cisenti",
    61: "hafif yagmurlu", 63: "yagmurlu", 65: "kuvvetli yagmurlu",
    71: "hafif karli", 73: "karli", 75: "yogun karli",
    80: "saganak", 81: "saganak", 82: "kuvvetli saganak",
    95: "gok gurultulu", 96: "dolu", 99: "dolu",
}


@mcp.tool()
def get_weather(city: str = "istanbul") -> str:
    """Bir sehrin hava durumunu soyler. Reports the weather for a Turkish city.
    Kullanici 'hava nasil', 'X'te hava nasil' dediginde cagir. Ucretsiz, anahtar gerekmez."""
    key = city.strip().lower()
    key = (key.replace("ı", "i").replace("ş", "s").replace("ğ", "g")
              .replace("ü", "u").replace("ö", "o").replace("ç", "c"))
    if key not in _TR_CITIES:
        return (f"'{city}' sehrini tanimiyorum. Su sehirler var: "
                + ", ".join(sorted(_TR_CITIES.keys())))
    lat, lon = _TR_CITIES[key]
    try:
        url = ("https://api.open-meteo.com/v1/forecast?"
               f"latitude={lat}&longitude={lon}"
               "&current=temperature_2m,weather_code,wind_speed_10m"
               "&daily=temperature_2m_max,temperature_2m_min&timezone=Europe%2FIstanbul")
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        cur = data["current"]
        daily = data["daily"]
        desc = _WMO.get(cur["weather_code"], "degisken")
        return (f"{city.capitalize()}: su an {round(cur['temperature_2m'])}°C, {desc}. "
                f"Bugun en yuksek {round(daily['temperature_2m_max'][0])}°C, "
                f"en dusuk {round(daily['temperature_2m_min'][0])}°C.")
    except Exception as exc:
        return f"Hava durumuna ulasamadim: {exc}"


# ---------------------------------------------------------------- PC kontrolu
#
# Iva'nin bilgisayarla etkilesime gecmesi: tarayici acma, web/YouTube arama.
# webbrowser modulu varsayilan tarayicida acar; komut CALISTIRMAZ (guvenli).

_KNOWN_SITES = {
    "google": "https://www.google.com",
    "youtube": "https://www.youtube.com",
    "youtube müzik": "https://music.youtube.com",
    "youtube muzik": "https://music.youtube.com",
    "gmail": "https://mail.google.com",
    "github": "https://github.com",
    "chatgpt": "https://chat.openai.com",
    "netflix": "https://www.netflix.com",
    "spotify": "https://open.spotify.com",
    "twitter": "https://twitter.com",
    "x": "https://x.com",
    "instagram": "https://www.instagram.com",
    "whatsapp": "https://web.whatsapp.com",
    "hava": "https://www.google.com/search?q=hava+durumu",
    "harita": "https://www.google.com/maps",
    "haritalar": "https://www.google.com/maps",
    "haberler": "https://news.google.com",
    "translate": "https://translate.google.com",
    "ceviri": "https://translate.google.com",
}


@mcp.tool()
def open_website(site: str) -> str:
    """Bilgisayarda tarayicida bir web sitesi acar. Opens a website in the PC browser.
    Kullanici 'X sitesini ac', 'google ac', 'youtube ac' dediginde cagir.
    site: bilinen bir isim (google, youtube, gmail...) ya da tam adres olabilir."""
    import webbrowser
    key = site.strip().lower()
    if key in _KNOWN_SITES:
        url = _KNOWN_SITES[key]
        label = site.strip()
    elif key.startswith("http://") or key.startswith("https://"):
        url = site.strip()
        label = url
    elif "." in key and " " not in key:
        url = "https://" + key
        label = key
    else:
        # Bilinmeyen isim -> Google'da aratip actiralim
        return web_search(site)
    webbrowser.open(url)
    return f"{label} tarayicida acildi."


@mcp.tool()
def web_search(query: str) -> str:
    """Bilgisayarda tarayicida Google aramasi acar. Opens a Google search in the browser.
    Kullanici 'sunu ara', 'google'da ara', 'internette ara' dediginde cagir."""
    import webbrowser
    url = "https://www.google.com/search?q=" + urllib.parse.quote(query)
    webbrowser.open(url)
    return f"'{query}' icin arama actim."


@mcp.tool()
def play_youtube(query: str) -> str:
    """YouTube'da arayip ilk videoyu bilgisayarda acar (muzik/video icin).
    Plays the first YouTube result. Kullanici 'X sarkisini ac', 'youtube'da X ac',
    'X muzigini cal' dediginde cagir. query: sarki/video adi."""
    import webbrowser
    # yt-dlp kutuphanesi varsa ilk videoyu bulup direkt ac (otomatik oynar)
    try:
        import yt_dlp
        opts = {"quiet": True, "no_warnings": True, "skip_download": True}
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
        entries = info.get("entries") if isinstance(info, dict) else None
        vid = entries[0].get("id") if entries else None
        if vid:
            webbrowser.open(f"https://www.youtube.com/watch?v={vid}")
            return f"'{query}' YouTube'da aciliyor, birazdan calmaya baslar."
    except Exception:
        pass
    # Fallback: arama sonuclarini ac
    url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(query)
    webbrowser.open(url)
    return f"'{query}' icin YouTube aramasi actim, oynatmak icin ilk videoya dokun."


# Bilinen uygulamalar - GUVENLIK: sadece bu listedekiler acilabilir, keyfi
# komut CALISTIRILMAZ. ("exe", isim) PATH'te aranir; ("uri", adres) ShellExecute.
_KNOWN_APPS = {
    "not defteri": ("exe", "notepad"), "notepad": ("exe", "notepad"),
    "hesap makinesi": ("exe", "calc"), "hesap makinasi": ("exe", "calc"),
    "calculator": ("exe", "calc"),
    "paint": ("exe", "mspaint"), "resim": ("exe", "mspaint"),
    "dosya gezgini": ("exe", "explorer"), "gezgin": ("exe", "explorer"),
    "explorer": ("exe", "explorer"), "dosyalar": ("exe", "explorer"),
    "gorev yoneticisi": ("exe", "taskmgr"), "task manager": ("exe", "taskmgr"),
    "ayarlar": ("uri", "ms-settings:"), "settings": ("uri", "ms-settings:"),
    "kontrol paneli": ("exe", "control"),
    "terminal": ("exe", "wt"), "komut istemi": ("exe", "cmd"),
    "spotify": ("uri", "spotify:"),
    "vs code": ("exe", "code"), "vscode": ("exe", "code"), "kod": ("exe", "code"),
    "discord": ("uri", "discord:"),
    "takvim": ("uri", "outlookcal:"), "saat": ("uri", "ms-clock:"),
    "kamera": ("uri", "microsoft.windows.camera:"),
}


SPOTIFY_CACHE = os.path.join(DATA_DIR, ".spotify_cache")
SPOTIFY_REDIRECT = "http://127.0.0.1:8888/callback"
SPOTIFY_SCOPE = "user-modify-playback-state user-read-playback-state"


def _spotify_client():
    """Premium + API anahtarlari ayarliysa gercek calma icin istemci dondurur;
    yoksa None (o zaman arama-acma moduna dusulur)."""
    cid = os.environ.get("SPOTIFY_CLIENT_ID", "").strip()
    secret = os.environ.get("SPOTIFY_CLIENT_SECRET", "").strip()
    if not cid or not secret or not os.path.exists(SPOTIFY_CACHE):
        return None
    try:
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth
        auth = SpotifyOAuth(client_id=cid, client_secret=secret,
                            redirect_uri=SPOTIFY_REDIRECT, scope=SPOTIFY_SCOPE,
                            cache_path=SPOTIFY_CACHE, open_browser=False)
        return spotipy.Spotify(auth_manager=auth)
    except Exception:
        return None


@mcp.tool()
def play_spotify(query: str) -> str:
    """Spotify'da bir sarkiyi bulup calar. Plays a song on Spotify.
    Kullanici 'spotify'da X cal/ac', 'spotify'dan X dinle' dediginde cagir.
    query: sarki veya sanatci adi. Premium + kurulum varsa dogrudan calar."""
    import os
    sp = _spotify_client()

    # Tam otomatik mod (Premium + API kurulu): ara ve aktif cihazda cal
    if sp is not None:
        try:
            res = sp.search(q=query, type="track", limit=1)
            items = res.get("tracks", {}).get("items", [])
            if not items:
                return f"Spotify'da '{query}' bulunamadi."
            tr = items[0]
            name = f"{tr['artists'][0]['name']} - {tr['name']}"
            devices = sp.devices().get("devices", [])
            if not devices:
                os.startfile("spotify:")
                return (f"'{name}' hazir ama once Spotify'in acilmasi gerek. "
                        f"Actim, birkac saniye sonra tekrar 'cal' de.")
            sp.start_playback(device_id=devices[0]["id"], uris=[tr["uri"]])
            return f"Spotify'da caliyor: {name}"
        except Exception as exc:
            return f"Spotify calma hatasi: {exc}. Spotify acik mi kontrol et."

    # Basit mod (kurulum yok): arama sayfasini ac
    try:
        os.startfile("spotify:search:" + urllib.parse.quote(query))
        return (f"Spotify'da '{query}' aramasini actim. Ilk sarkiya dokununca "
                f"calmaya baslar.")
    except Exception:
        import webbrowser
        webbrowser.open("https://open.spotify.com/search/" +
                        urllib.parse.quote(query))
        return f"Spotify web'de '{query}' aramasini actim."


@mcp.tool()
def open_app(app: str) -> str:
    """Bilgisayarda bir uygulama acar. Opens a known desktop application.
    Kullanici 'X uygulamasini ac', 'not defteri ac', 'hesap makinesi ac',
    'spotify ac' dediginde cagir. Sadece bilinen uygulamalar acilir."""
    import os
    import subprocess
    key = app.strip().lower()
    if key not in _KNOWN_APPS:
        opts = ", ".join(sorted(set(
            k for k in _KNOWN_APPS if " " not in k or len(k) < 14))[:12])
        return (f"'{app}' uygulamasini tanimiyorum. Acabildiklerim ornek: {opts}. "
                f"Web sitesi istiyorsan onu da acabilirim.")
    kind, target = _KNOWN_APPS[key]
    try:
        if kind == "uri":
            os.startfile(target)
        else:
            subprocess.Popen([target], shell=False)
        return f"{app} aciliyor."
    except FileNotFoundError:
        return f"{app} bu bilgisayarda kurulu degil gibi gorunuyor."
    except Exception as exc:
        return f"{app} acilamadi: {exc}"


# ---------------------------------------------------------------- daily digest

def _digest_loop():
    digest_hour = int(os.environ.get("DIGEST_HOUR", "21") or 21)
    while True:
        try:
            state = _load_json(STATE_FILE, {})
            now = _now()
            today = _today_str()
            if now.hour == digest_hour and state.get("last_digest") != today:
                parts = [f"🌙 Iva gunluk ozet - {today}"]
                content = _read_notes(today)
                if content:
                    parts.append("\n📝 Notlar:\n" + content)
                open_tasks = [t for t in _load_json(TASKS_FILE, [])
                              if not t.get("done")]
                if open_tasks:
                    parts.append("\n✅ Bekleyen gorevler:\n" +
                                 "\n".join(f"- {t['text']}" for t in open_tasks[:10]))
                parts.append("\nBugun nasil gecti? Anlatirsan gunlugune yazarim.")
                ok, _ = _telegram_send("\n".join(parts))
                if ok:
                    state["last_digest"] = today
                    _save_json(STATE_FILE, state)
        except Exception:
            pass
        threading.Event().wait(60)


def _backup_loop():
    # Gunde bir kez veri klasorunu zip'ler; son 7 yedegi tutar.
    while True:
        try:
            state = _load_json(STATE_FILE, {})
            today = _today_str()
            if state.get("last_backup") != today:
                stamp = _now().strftime("%Y%m%d")
                target = os.path.join(BACKUP_DIR, f"iva-data-{stamp}")
                # backups klasorunu disarida tutmak icin gecici bir liste yerine
                # dogrudan data altindaki dosyalari zip'liyoruz
                shutil.make_archive(target, "zip", DATA_DIR, ".")
                state["last_backup"] = today
                _save_json(STATE_FILE, state)
                backups = sorted(
                    [f for f in os.listdir(BACKUP_DIR) if f.endswith(".zip")])
                for old in backups[:-7]:
                    try:
                        os.remove(os.path.join(BACKUP_DIR, old))
                    except OSError:
                        pass
        except Exception:
            pass
        threading.Event().wait(3600)


# Arka plan izleyicileri: hatirlaticilar ve yedek Telegram olmadan da anlamli
# (yukleme/yedek), digest Telegram gerektirir ama kontrolu kendi icinde yapar.
for _target in (_reminder_loop, _digest_loop, _backup_loop):
    threading.Thread(target=_target, daemon=True).start()


# ---------------------------------------------------------------- utilities

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval(node):
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("Desteklenmeyen ifade")


@mcp.tool()
def calculator(expression: str) -> str:
    """Matematik islemi hesaplar. Calculates a math expression.
    Ornek/example: '127*43', '(5+3)/2', '2**10'"""
    try:
        result = _safe_eval(ast.parse(expression, mode="eval"))
        return f"{expression} = {result}"
    except Exception:
        return "Bu ifadeyi hesaplayamadim. Sadece sayilar ve + - * / ** % kullanilabilir."


@mcp.tool()
def get_datetime() -> str:
    """Su anki tarih ve saati soyler. Returns current date and time."""
    now = _now()
    return f"{now.strftime('%d.%m.%Y %H:%M')} {DAYS_TR[now.weekday()]}"


@mcp.tool()
def roll_dice(sides: int = 6) -> str:
    """Zar atar. Rolls a die with the given number of sides (default 6)."""
    sides = max(2, min(int(sides), 1000))
    return f"{sides} yuzlu zar atildi: {random.randint(1, sides)}"


@mcp.tool()
def disk_status() -> str:
    """Bilgisayarin C diskindeki bos alani soyler. Reports free disk space on C:."""
    usage = shutil.disk_usage("C:\\")
    free_gb = usage.free / (1024 ** 3)
    total_gb = usage.total / (1024 ** 3)
    return f"C diski: {free_gb:.1f} GB bos / toplam {total_gb:.0f} GB"


if __name__ == "__main__":
    mcp.run(transport="stdio")
