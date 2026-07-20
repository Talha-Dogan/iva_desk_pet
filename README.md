# İva — Konuşan Masa Robotu 🤖

ESP32-S3 tabanlı, Türkçe konuşan, duygularını yüzüyle gösteren masaüstü yapay zekâ arkadaşı.
[xiaozhi-esp32](https://github.com/78/xiaozhi-esp32) projesi üzerine kurulmuş; kendi yüz motoru,
Türkçe beyin ve kişisel asistan araçlarıyla genişletilmiştir.

## Neler yapabiliyor?

- 🎙️ **Sesle uyanır** — "Jarvis" veya "Computer" (aynı anda iki kelime aktif)
- 🇹🇷 **Türkçe konuşur** — Türkçe firmware + Türkçe ses (Edge TTS)
- 😊 **Duygularını gösterir** — 21 duygu, animasyonlu göz/kaş/ağız (mutlu, üzgün, kızgın, şaşkın...)
- 👄 **Gerçek dudak senkronu** — ağız, hoparlöre giden sesin gücüne göre hareket eder
- 😴 **Uyur** — "uyu" dendiğinde gözlerini kapatır, uyandırma kelimesine kadar uyanmaz
- 📝 **Not alır** — sesli not, arama, günlük döküm
- 📨 **Telegram'a yazar** — notları gönderir, her akşam otomatik özet geçer
- 🧠 **Mod günlüğü tutar** — ruh halini kaydeder, geçmişini raporlar
- 📊 **Projeleri hatırlar** — durumlarını takip eder, sorar
- ⏰ **Hatırlatıcı kurar**, hesap yapar, tarih/saat söyler
- 🖥️ **Ekran değiştirir** — "durum ekranını göster" / "yüzünü göster"

## Mimari

```
┌──────────────┐   ses    ┌──────────────┐   araçlar   ┌──────────────┐
│  ESP32-S3    │ ───────► │   Sunucu     │ ──────────► │ Iva Araçları │
│  (firmware)  │ ◄─────── │ (bulut/yerel)│ ◄────────── │  (MCP/Python)│
└──────────────┘  yanıt   └──────────────┘             └──────────────┘
   yüz + mikrofon           ASR→LLM→TTS                not/Telegram/mod
   + hoparlör + OLED
```

İki sunucu seçeneği desteklenir:

| | Resmî sunucu (xiaozhi.me) | Kendi sunucun (`server/`) |
|---|---|---|
| Kurulum | Kolay, hesap açman yeter | Docker + API anahtarı |
| Türkçe ses tanıma | Sınırlı | Groq Whisper (çok iyi) |
| Müzik | Çince katalog | Kendi mp3'lerin |
| Gizlilik | Bulutta | Tamamen yerel ağda |
| Bağlılık | İnternet | PC açık olmalı |

## Klasörler

| Klasör | İçerik |
|---|---|
| [`firmware/`](firmware/) | ESP32 tarafı: yüz motoru, kart yapılandırması, değiştirilmiş dosyalar |
| [`bridge/`](bridge/) | İva'nın araçları (MCP sunucusu): not, Telegram, mod, proje, hatırlatıcı |
| [`server/`](server/) | Kendi sunucun: Docker yapılandırması, Türkçe ASR/LLM/TTS ayarları, testler |
| [`docs/`](docs/) | Donanım şeması ve mimari notları |

## Hızlı başlangıç

Yeni bir bilgisayarda tek komutla kurulur:

```powershell
git clone https://github.com/Talha-Dogan/iva_desk_pet.git
cd iva_desk_pet
powershell -ExecutionPolicy Bypass -File setup.ps1
```

Betik sanal ortamı kurar, bağımlılıkları yükler, `.env` şablonunu hazırlar ve
Windows açılışına otomatik başlatma ekler. Ardından `bridge\.env` dosyasına
anahtarlarını yazman yeterli. Ayrıntılar: [docs/kurulum.md](docs/kurulum.md)

Diğer belgeler:

1. **Donanım:** [docs/donanim.md](docs/donanim.md) — kablolama şeması
2. **Firmware:** [firmware/README.md](firmware/README.md) — derleme ve yükleme
3. **Araçlar:** [bridge/README.md](bridge/README.md) — not/Telegram sistemi
4. **Kendi sunucun (opsiyonel):** [server/README.md](server/README.md)
5. **Mimari:** [docs/mimari.md](docs/mimari.md) — tasarım kararları

## Donanım

| Parça | Model | Not |
|---|---|---|
| Kart | ESP32-S3 Zero | 4MB flash, 2MB PSRAM (quad) |
| Mikrofon | INMP441 | I2S dijital |
| Amfi | MAX98357A | I2S dijital |
| Ekran | SSD1306 OLED | 128x64, I2C |

> **Not:** 4MB flash bazı özellikleri kısıtlar (OTA güncelleme ve özel uyandırma kelimesi yok).
> 16MB'lık bir S3 kartı bu kısıtları kaldırır.

## Yol haritası

- [x] Türkçe firmware + iki uyandırma kelimesi
- [x] Duygulara tepki veren animasyonlu yüz
- [x] Gerçek dudak senkronu, düşük güç ekran çizimi
- [x] Not / Telegram / mod / proje / hatırlatıcı araçları
- [x] Kendi sunucu (Türkçe ASR + TTS, test edildi)
- [x] Windows açılışında otomatik başlatma + tek komutluk kurulum
- [ ] Kalıcı hatırlatıcılar ve veri yedeği
- [ ] Sesli oyunlar ve Pomodoro modu
- [ ] Ders/toplantı kayıt ve özet modu
- [ ] Home Assistant ile akıllı ev kontrolü
- [ ] 3D baskı kasa

## Lisans ve teşekkür

MIT. Bu proje şunların üzerine kuruludur:

- [78/xiaozhi-esp32](https://github.com/78/xiaozhi-esp32) (MIT) — ana firmware
- [xinnan-tech/xiaozhi-esp32-server](https://github.com/xinnan-tech/xiaozhi-esp32-server) — kendi sunucu
- [TechTalkies/Face-for-Xiaozhi](https://github.com/TechTalkies/Face-for-Xiaozhi) (MIT) — yüz motorunun ilk fikri
- Göz animasyonu tasarımında Anki Cozmo/Vector prensiplerinden ilham alınmıştır
