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
import urllib.request

from mcp.server.fastmcp import FastMCP

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
NOTES_DIR = os.path.join(DATA_DIR, "notes")
MOOD_FILE = os.path.join(DATA_DIR, "mood_log.jsonl")
PROJECTS_FILE = os.path.join(DATA_DIR, "projects.json")
STATE_FILE = os.path.join(DATA_DIR, "state.json")

os.makedirs(NOTES_DIR, exist_ok=True)


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
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------- notes

@mcp.tool()
def save_note(text: str, category: str = "genel") -> str:
    """Kullanicinin notunu kaydeder. Saves a note for the user.
    Kullanici 'not al', 'bunu kaydet', 'unutmayayim' gibi seyler dediginde cagir.
    category: ders, toplanti, fikir, yapilacak veya genel olabilir."""
    now = _now()
    path = _note_path(_today_str())
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
    with open(MOOD_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
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

@mcp.tool()
def set_reminder(minutes: int, message: str) -> str:
    """Hatirlatici kurar; suresi gelince Telegram'dan mesaj gider. Sets a reminder.
    Kullanici 'X dakika sonra hatirlat' dediginde cagir. minutes: kac dakika sonra."""
    token, chat_id = _telegram_config()
    if not token or not chat_id:
        return "Hatirlatici icin once Telegram ayarlanmali (.env)."
    minutes = max(1, min(int(minutes), 24 * 60))

    def fire():
        _telegram_send(f"Hatirlatma: {message}")

    timer = threading.Timer(minutes * 60, fire)
    timer.daemon = True
    timer.start()
    return f"{minutes} dakika sonra Telegram'dan hatirlatacagim."


# ---------------------------------------------------------------- daily digest

def _digest_loop():
    digest_hour = int(os.environ.get("DIGEST_HOUR", "21") or 21)
    while True:
        try:
            state = _load_json(STATE_FILE, {})
            now = _now()
            today = _today_str()
            if now.hour == digest_hour and state.get("last_digest") != today:
                content = _read_notes(today)
                if content:
                    ok, _ = _telegram_send(f"Iva gunluk ozet - {today}:\n\n{content}")
                    if ok:
                        state["last_digest"] = today
                        _save_json(STATE_FILE, state)
                else:
                    state["last_digest"] = today
                    _save_json(STATE_FILE, state)
        except Exception:
            pass
        threading.Event().wait(60)


_token, _chat = _telegram_config()
if _token and _chat:
    _digest_thread = threading.Thread(target=_digest_loop, daemon=True)
    _digest_thread.start()


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
