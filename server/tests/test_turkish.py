"""Iva sunucusu - Turkce zincir testi (cihaza gerek yok).

1) EdgeTTS ile Turkce cumle seslendirilir      -> TTS testi
2) Uretilen ses Groq Whisper'a gonderilir       -> ASR testi
3) Metin Groq LLM'e sorulur                     -> beyin testi
"""
import asyncio
import os
import sys

import requests
import yaml

CONFIG = "/opt/xiaozhi-esp32-server/data/.config.yaml"
OUT = "/opt/xiaozhi-esp32-server/tmp/tr_test.mp3"
CUMLE = "Merhaba, benim adim Iva. Bugun hava nasil olacak?"


def main():
    with open(CONFIG, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    voice = cfg["TTS"]["EdgeTTS"]["voice"]
    asr = cfg["ASR"]["GroqASR"]
    llm = cfg["LLM"]["GroqLLM"]

    # 1) TTS
    import edge_tts
    print(f"[1/3] TTS deneniyor (ses: {voice}) ...")
    asyncio.run(edge_tts.Communicate(CUMLE, voice).save(OUT))
    size = os.path.getsize(OUT)
    if size < 1000:
        print("  HATA: ses dosyasi olusmadi")
        sys.exit(1)
    print(f"  OK - {size} bayt ses uretildi")

    # 2) ASR
    print("[2/3] ASR deneniyor (Groq Whisper) ...")
    with open(OUT, "rb") as f:
        r = requests.post(
            asr["base_url"],
            headers={"Authorization": f"Bearer {asr['api_key']}"},
            files={"file": ("tr_test.mp3", f, "audio/mpeg")},
            data={"model": asr["model_name"], "language": "tr"},
            timeout=60,
        )
    if r.status_code != 200:
        print(f"  HATA {r.status_code}: {r.text[:300]}")
        sys.exit(1)
    metin = r.json().get("text", "").strip()
    print(f"  OK - taninan metin: {metin}")

    # 3) LLM
    print("[3/3] LLM deneniyor (Groq) ...")
    url = llm["url"].rstrip("/") + "/chat/completions"
    r = requests.post(
        url,
        headers={"Authorization": f"Bearer {llm['api_key']}",
                 "Content-Type": "application/json"},
        json={
            "model": llm["model_name"],
            "messages": [
                {"role": "system", "content": "Sen Iva adinda sevimli bir masa robotusun. Sadece Turkce, tek cumle cevap ver."},
                {"role": "user", "content": metin or CUMLE},
            ],
            "max_tokens": 100,
        },
        timeout=60,
    )
    if r.status_code != 200:
        print(f"  HATA {r.status_code}: {r.text[:300]}")
        sys.exit(1)
    cevap = r.json()["choices"][0]["message"]["content"].strip()
    print(f"  OK - Iva'nin cevabi: {cevap}")

    print("\nSONUC: Turkce zincir calisiyor (TTS + ASR + LLM).")


if __name__ == "__main__":
    main()
