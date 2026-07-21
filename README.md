<!-- ============================================================= -->
<!--  GORSEL: Buraya İva'nın ana fotoğrafı/gif'i (yüz ekranı açık, masada)  -->
<!--  Yüklemek icin: docs/media/ klasorune koy, sonra asagidaki satiri ac:   -->
<!--  <p align="center"><img src="docs/media/iva-hero.gif" width="480"></p>  -->
<!-- ============================================================= -->

# İva — Konuşan Masa Robotu 🤖

> ESP32-S3 tabanlı, Türkçe konuşan, duygularını yüzüyle gösteren, not alıp Telegram'a yazan masaüstü yapay zekâ arkadaşı.

İva; sesle uyanır, seninle Türkçe sohbet eder, konuşurken duygusuna göre yüz ifadesi değiştirir,
sözünü kesip yeni komut verebilirsin, not tutar, hatırlatma kurar ve her akşam gününü Telegram'a özetler.
[xiaozhi-esp32](https://github.com/78/xiaozhi-esp32) projesi üzerine kurulmuş; kendi yüz motoru,
Türkçe beyin ve kişisel asistan araçlarıyla genişletilmiştir.

<!-- Rozet satırı (istege bagli, suslu durur) -->
`ESP32-S3` · `ESP-IDF 5.5` · `Türkçe` · `MCP` · `Python` · `Docker`

---

## 📑 İçindekiler

- [Ne yapabiliyor?](#-ne-yapabiliyor)
- [Nasıl çalışıyor? (mimari)](#-nasıl-çalışıyor-mimari)
- [Hangi parça neye bağlı?](#-hangi-parça-neye-bağlı)
- [Kurulum](#-kurulum)
- [Donanım](#-donanım)
- [Yüz motoru](#-yüz-motoru)
- [İva'nın araçları](#-i̇vanın-araçları)
- [Sesli komut sözlüğü](#-sesli-komut-sözlüğü)
- [Klasör yapısı](#-klasör-yapısı)
- [Yol haritası](#-yol-haritası)
- [Lisans ve teşekkür](#-lisans-ve-teşekkür)

---

## ✨ Ne yapabiliyor?

| | Özellik | Açıklama |
|---|---|---|
| 🎙️ | **Sesle uyanma** | "Jarvis" veya "Computer" — aynı anda iki kelime aktif |
| ✋ | **Sözünü kesme (barge-in)** | İva uzun konuşurken uyandırma kelimesini duyunca durup seni dinler |
| 🇹🇷 | **Türkçe konuşma** | Türkçe firmware + Türkçe ses (Edge TTS "Emel") |
| 😊 | **Duygulu yüz** | 21 duygu → animasyonlu göz/kaş/ağız (mutlu, üzgün, kızgın, şaşkın, aşık...) |
| 👄 | **Gerçek dudak senkronu** | Ağız, hoparlöre giden sesin şiddetine göre hareket eder |
| 😴 | **Gerçek uyku** | "uyu" deyince veda edip gözlerini kapatır; uyandırma kelimesine kadar uyanmaz |
| 📝 | **Not sistemi** | Sesli not, arama, günlük döküm |
| 📨 | **Telegram** | Notları gönderir, her akşam otomatik gün özeti geçer |
| ⏰ | **Kalıcı hatırlatıcılar** | "her gün 9'da ilaç hatırlat" — PC kapansa bile kaybolmaz |
| 🍅 | **Pomodoro** | "25 dakika odaklanacağım" → süre bitince Telegram'dan haber |
| 🧠 | **Mod & alışkanlık takibi** | "bugün yorgunum", "bugün spor yaptım" → seri tutar |
| 📊 | **Proje hafızası** | Projelerinin durumunu hatırlar, sorar |
| 🌤️ | **Hava durumu** | 12 Türk şehri, API anahtarı gerektirmez |
| 🖥️ | **Ekran geçişi** | "durum ekranını göster" / "yüzünü göster" |
| 💻 | **PC kontrolü** | "Google aç", "YouTube'da X şarkısını aç", "internette ... ara" |

<!-- ============================================================= -->
<!--  GORSEL: 3-4'lu kare gif kolajı önerilir:                              -->
<!--    mutlu yüz | üzgün yüz | konuşurken ağız | uyku (zzz)                 -->
<!--  docs/media/ altina koyup asagiyi ac:                                  -->
<!--  | ![mutlu](docs/media/happy.gif) | ![üzgün](docs/media/sad.gif) |     -->
<!--  |---|---|                                                              -->
<!--  | ![konuşma](docs/media/talk.gif) | ![uyku](docs/media/sleep.gif) |   -->
<!-- ============================================================= -->

---

## 🔧 Nasıl çalışıyor? (mimari)

İva üç parçadan oluşur ve her biri farklı yerde çalışır:

```
   ┌─────────────────┐      ses       ┌──────────────────┐    araç çağrısı   ┌────────────────┐
   │   ESP32-S3      │ ─────────────► │     SUNUCU        │ ────────────────► │  İVA ARAÇLARI  │
   │   (cihaz)       │                │  (bulut / yerel)  │                   │  (senin PC'n)  │
   │                 │ ◄───────────── │                   │ ◄──────────────── │                │
   └─────────────────┘   sesli yanıt  └──────────────────┘    araç sonucu     └────────────────┘
    mikrofon · hoparlör                 ASR → LLM → TTS         MCP protokolü    not · Telegram
    OLED yüz · uyandırma                 (konuşmayı anlar,                        mod · hatırlatıcı
    kelimesi (offline)                   düşünür, seslendirir)                    hava · pomodoro
```

**Adım adım bir konuşma:**

1. **"Jarvis"** dersin → cihaz bunu **kendi içinde** (internetsiz) algılar, uyanır
2. Konuşman ses olarak **sunucuya** gider
3. Sunucu sırayla: sesi yazıya çevirir (**ASR**) → cevabı üretir (**LLM**) → yazıyı sese çevirir (**TTS**)
4. Cevap sana **sesli** döner, yüz de duyguya göre değişir
5. Cevap bir iş gerektiriyorsa ("not al") sunucu **İva Araçları'na** komut yollar (MCP)

> **Önemli:** Cihazda çalışan tek yapay zekâ parçası uyandırma kelimesidir. Geri kalan her şey
> sunucudadır — bu yüzden cihaz internetsiz sohbet edemez.

### İki sunucu seçeneği

| | Resmî sunucu (xiaozhi.me) | Kendi sunucun (`server/`) |
|---|---|---|
| **Kurulum** | Kolay — hesap açman yeter | Docker + ücretsiz Groq anahtarı |
| **Türkçe ses tanıma** | Sınırlı | Groq Whisper (çok iyi) |
| **Ses (TTS)** | Konsoldan seçilir | Türkçe Edge TTS |
| **Müzik** | Çince katalog | Kendi mp3'lerin |
| **Gizlilik** | Bulutta işlenir | Tamamen yerel ağda |
| **Bağımlılık** | İnternet | PC + Docker açık olmalı |

---

## 🧩 Hangi parça neye bağlı?

Sistemin çalışması için **neyin açık olması gerektiği** — sorun çıkınca buraya bak:

| Özellik | Çalışması için gereken |
|---|---|
| Uyanma, temel yüz animasyonu | Sadece cihaz (elektrik) — internetsiz çalışır |
| Sohbet (konuşma/dinleme) | Cihaz + WiFi + sunucu (resmî ya da kendi) |
| Türkçe cevap sesi | Sunucudaki TTS ayarı (resmî: konsol, kendi: Edge TTS) |
| Not / Telegram / hatırlatıcı araçları | **Köprü açık olmalı** (`start_iva_bridge.bat`) + `.env` dolu |
| Telegram'a mesaj | Köprü + geçerli `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` |
| Kendi sunucu (Türkçe Whisper, müzik) | Docker Desktop açık + `iva-server` konteyneri + Groq anahtarı |
| Otomatik günlük özet (21:00) | Köprü o saatte açık olmalı |

**Bağımlılık zinciri kısaca:**

```
Cihaz ──WiFi──► Sunucu ──MCP──► Köprü ──► Telegram / dosyalar
  │               │                │
elektrik      internet+        PC açık +
              (Docker)         .env dolu
```

<!-- ============================================================= -->
<!--  GORSEL: İstersen buraya kendi çizdiğin/çektiğin bağlantı şemasının     -->
<!--  fotoğrafını koyabilirsin: docs/media/baglanti-semasi.jpg              -->
<!-- ============================================================= -->

---

## 🚀 Kurulum

Yeni bir bilgisayarda **tek komutla** kurulur:

```powershell
git clone https://github.com/Talha-Dogan/iva_desk_pet.git
cd iva_desk_pet
powershell -ExecutionPolicy Bypass -File setup.ps1
```

Bu betik: sanal ortamı kurar, bağımlılıkları yükler, `.env` şablonunu hazırlar ve
Windows açılışına otomatik başlatma ekler. Ardından `bridge\.env` dosyasına anahtarlarını
yazman yeterli.

Adım adım anlatım ve sorun giderme: **[docs/kurulum.md](docs/kurulum.md)**

Diğer belgeler:
- 🔌 [docs/donanim.md](docs/donanim.md) — kablolama şeması
- 💾 [firmware/README.md](firmware/README.md) — firmware derleme ve yükleme
- 🛠️ [bridge/README.md](bridge/README.md) — araçlar (not/Telegram/mod)
- 🖥️ [server/README.md](server/README.md) — kendi sunucun
- 🧠 [docs/mimari.md](docs/mimari.md) — tasarım kararları ("neden böyle yapıldı")

---

## 🔌 Donanım

| Parça | Model | Not |
|---|---|---|
| Kart | ESP32-S3 Zero | 4MB flash, 2MB PSRAM (quad) |
| Mikrofon | INMP441 | I2S dijital |
| Amfi | MAX98357A | I2S dijital |
| Ekran | SSD1306 OLED | 128x64, I2C |

<!-- ============================================================= -->
<!--  GORSEL: Breadboard'un fotoğrafı buraya çok yakışır                    -->
<!--  docs/media/donanim.jpg                                                -->
<!-- ============================================================= -->

**Pin bağlantıları:**

| Parça | Bacak → GPIO |
|---|---|
| Mikrofon (INMP441) | SD→6, WS→7, SCK→8 |
| Amfi (MAX98357A) | DIN→12, BCLK→11, LRC→10, GAIN→GND |
| OLED (SSD1306) | SDA→4, SCL→3 |
| Dahili RGB LED | 21 |

> **Not:** 4MB flash bazı özellikleri kısıtlar (kablosuz güncelleme ve özel "iva" uyandırma
> kelimesi yok). 16MB'lık bir S3 kartı bu kısıtları kaldırır.

---

## 😊 Yüz motoru

Sıfırdan yazılmış animasyonlu yüz; [Anki Cozmo/Vector](https://www.fastcompany.com/3061276/meet-cozmo-the-pixar-inspired-ai-powered-robot-that-feels)
prensiplerinden ilham alır.

- **Durumlar:** Bekleme (gezinen bakış, göz kırpma) → Dinleme (gözler büyür) →
  Konuşma (sese göre ağız) → Uyku (kapalı gözler, nefes alma)
- **Duygular:** Sunucudan gelen duygu etiketi 10 yüz ifadesine eşlenir; 12 saniye sonra
  doğal ifadeye döner
- **Enerji dostu:** Ekranda yalnızca göz/ağız yanar (arka plan sönük)

<!-- ============================================================= -->
<!--  GORSEL: Duygu ifadelerinin yakın çekim gif'i çok etkileyici olur      -->
<!--  Öneri: her duygu için kısa gif, tablo halinde:                        -->
<!--  | Mutlu | Üzgün | Kızgın | Şaşkın |                                    -->
<!--  |-------|-------|--------|--------|                                    -->
<!--  docs/media/emotion-*.gif                                              -->
<!-- ============================================================= -->

Nasıl çalıştığının detayı: [firmware/README.md](firmware/README.md#yüz-motoru-nasıl-çalışır)

---

## 🛠️ İva'nın araçları

Köprü (`bridge/`) üzerinden yapay zekâya açılan **27 araç**. Tam liste ve örnek komutlar:
[bridge/README.md](bridge/README.md)

Kategoriler: **notlar**, **görevler & odak (Pomodoro)**, **kalıcı hatırlatıcılar**,
**kişisel takip** (mod/günlük/alışkanlık/proje), **hava durumu**, ve **temel araçlar**
(hesap makinesi, saat, zar).

---

## 🗣️ Sesli komut sözlüğü

Sık kullanılan komutların örnekleri (İva resmî ya da kendi sunucunda, köprü açıkken):

| Söyle | İva ne yapar |
|---|---|
| "Jarvis" / "Computer" | Uyanır ve dinler |
| *(konuşurken)* "Jarvis" | Durur, seni dinler |
| "uyu" / "uyan" | Uyur / uyanır |
| "not al: ..." | Not kaydeder |
| "bugün ne not aldım?" | Notları okur |
| "notları Telegram'a gönder" | Gruba gönderir |
| "listeye ekle: ..." | Görev ekler |
| "25 dakika odaklanacağım" | Pomodoro başlatır |
| "her gün 9'da ilaç hatırlat" | Kalıcı hatırlatıcı kurar |
| "bugün yorgunum" | Modunu kaydeder |
| "İstanbul'da hava nasıl?" | Hava durumu |
| "durum ekranını göster" | Bilgi ekranına geçer |
| "Google aç" / "YouTube aç" | PC'de tarayıcıda siteyi açar |
| "Tarkan Kuzu Kuzu'yu aç" | YouTube'da bulup çalar |
| "internette ... ara" | PC'de Google araması açar |

---

## 💻 PC kontrolü

İva, senin bilgisayarınla etkileşime girebilir — tarayıcı açar, YouTube'da şarkı bulup çalar,
web araması yapar. Bunun için ekstra bir kurulum gerekmez; araçlar zaten köprüde (`bridge/`) çalışır.

| Söyle | Ne olur |
|---|---|
| "Google aç", "YouTube aç", "Spotify aç", "Gmail aç" | Site PC'de açılır (bilinen ~15 site hazır) |
| "... şarkısını aç", "YouTube'da ... aç" | yt-dlp ile ilk video bulunur, açılır ve **çalmaya başlar** |
| "internette ... ara", "Google'da ... ara" | Google araması açılır |

**Nasıl çalışır?** Cihaz komutu anlamaz — "YouTube aç" isteği sunucudan senin PC'ndeki köprüye
gider, köprü tarayıcıyı açar. Yani ESP32'ye kod yüklemeye gerek yok; yeni PC yeteneği eklemek
sadece köprüdeki `tools.py`'yi değiştirmektir.

> **Güvenlik:** Bu araçlar yalnızca web sayfası açar — komut çalıştırmaz, dosya silmez.
> İva'nın PC erişimi sınırlı ve güvenli bir çerçevededir.

**Not:** Yeni araç eklendiğinde cihaz bir kez yeniden başlatılmalı (güncel araç listesini
oturum başında alır). Konsolda MCP Endpoint durumu "Connected" olmalı; "Not Connected" ise
`.env`'deki endpoint token'ı eskimiş olabilir (xiaozhi bunları yeniler) — konsoldaki güncel
adresi `.env`'e yapıştırıp köprüyü yeniden başlat.

---

## 📁 Klasör yapısı

| Klasör | İçerik |
|---|---|
| [`firmware/`](firmware/) | ESP32 tarafı: yüz motoru, pin haritası, değiştirilmiş kaynaklar |
| [`bridge/`](bridge/) | İva'nın araçları (MCP sunucusu) |
| [`server/`](server/) | Kendi sunucun: Docker + Türkçe ASR/LLM/TTS + testler |
| [`scripts/`](scripts/) | Kurulum, otomatik başlatma, repo senkron betikleri |
| [`docs/`](docs/) | Donanım, mimari, kurulum belgeleri |

> Bu repo çalışma klasörünün **düzenlenmiş kopyasıdır** — 1 GB'lık firmware ağacını değil,
> yalnızca yazdığımız/değiştirdiğimiz dosyaları içerir. Gizli anahtarlar `.gitignore` ile dışarıda.

---

## 🗺️ Yol haritası

- [x] Türkçe firmware + iki uyandırma kelimesi
- [x] Duygulara tepki veren animasyonlu yüz
- [x] Gerçek dudak senkronu, düşük güç ekran çizimi
- [x] Sözünü kesme (barge-in)
- [x] 30 araç: not / Telegram / mod / hatırlatıcı / Pomodoro / hava
- [x] PC kontrolü: tarayıcı açma, YouTube'da şarkı çalma, web arama
- [x] Kalıcı hatırlatıcılar + otomatik yedekleme
- [x] Kendi sunucu (Türkçe ASR + TTS, test edildi)
- [x] Windows açılışında otomatik başlatma + tek komutluk kurulum
- [ ] Ders/toplantı kayıt ve özet modu
- [ ] Sesli oyunlar (bilmece, 20 soru)
- [ ] Home Assistant ile akıllı ev kontrolü
- [ ] Kendi müzik arşivi (kendi sunucuda)
- [ ] 3D baskı kasa + 16MB karta geçiş

---

## 📜 Lisans ve teşekkür

MIT. Bu proje şunların üzerine kuruludur:

- [78/xiaozhi-esp32](https://github.com/78/xiaozhi-esp32) (MIT) — ana firmware
- [xinnan-tech/xiaozhi-esp32-server](https://github.com/xinnan-tech/xiaozhi-esp32-server) — kendi sunucu
- [TechTalkies/Face-for-Xiaozhi](https://github.com/TechTalkies/Face-for-Xiaozhi) (MIT) — yüz motorunun ilk fikri
- Göz animasyonunda Anki Cozmo/Vector tasarım prensiplerinden ilham alınmıştır

---

<p align="center"><i>Talha'nın masasında yaşıyor 🤖</i></p>
