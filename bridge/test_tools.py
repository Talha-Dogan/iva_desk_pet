"""Tum Iva araclarini import edip dogrudan cagirarak test eder.

Telegram gonderimi ve MCP baglantisi olmadan calisir; sadece arac mantigini
sinar. Kendi klasorunde calistir:
    venv\\Scripts\\python.exe test_tools.py
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# Telegram'i devre disi birak (test sirasinda gercek mesaj gitmesin)
os.environ["TELEGRAM_BOT_TOKEN"] = ""
os.environ["TELEGRAM_CHAT_ID"] = ""

spec = importlib.util.spec_from_file_location("tools", os.path.join(HERE, "tools.py"))
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)

ok_count = 0
err_count = 0


def show(label, fn, *a, **k):
    global ok_count, err_count
    try:
        r = fn(*a, **k)
        print(f"OK  {label}: {str(r)[:80]}")
        ok_count += 1
    except Exception as e:
        print(f"HATA {label}: {type(e).__name__}: {e}")
        err_count += 1


# Gorevler
show("add_task", t.add_task, "test gorevi")
show("list_tasks", t.list_tasks)
show("complete_task", t.complete_task, 1)
# Odak
show("start_pomodoro", t.start_pomodoro, 25, "kodlama")
# Gunluk
show("add_journal", t.add_journal, "test gunluk")
show("read_journal", t.read_journal, 7)
# Aliskanlik
show("track_habit", t.track_habit, "spor")
show("habit_status", t.habit_status)
# Hava
show("get_weather", t.get_weather, "istanbul")
show("get_weather-bilinmeyen", t.get_weather, "Paris")
# Hatirlatici (Telegram kapali)
show("set_reminder", t.set_reminder, 5, "test")
show("list_reminders", t.list_reminders)
# Notlar
show("save_note", t.save_note, "regresyon", "genel")
show("read_today_notes", t.read_today_notes)
# Mod / proje
show("log_mood", t.log_mood, "iyi", 8, "test")
show("get_mood_history", t.get_mood_history, 7)
show("update_project", t.update_project, "iva", "gelistiriliyor")
show("list_projects", t.list_projects)
# Yardimci
show("calculator", t.calculator, "127*43")
show("get_datetime", t.get_datetime)

print(f"\nSONUC: {ok_count} OK, {err_count} HATA")
sys.exit(1 if err_count else 0)
