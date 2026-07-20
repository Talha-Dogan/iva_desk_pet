# Firmware — ESP32-S3 tarafı

Bu klasör **tüm firmware'i değil**, [xiaozhi-esp32](https://github.com/78/xiaozhi-esp32) v2
üzerinde değiştirilen/eklenen dosyaları içerir. Böylece kendi kodumuz üstteki projeden ayrı durur.

## Kurulum

1. ESP-IDF **v5.5.x** kur ([EIM](https://dl.espressif.com/dl/esp-idf/) ile en kolayı)
2. Ana projeyi klonla:
   ```bash
   git clone https://github.com/78/xiaozhi-esp32.git
   ```
3. Bu klasördeki `main/` altındaki dosyaları, klonladığın projenin `main/` klasörüne
   **aynı yollara** kopyala (üzerine yaz)
4. `sdkconfig.iva` dosyasını proje kökine `sdkconfig` adıyla kopyala
5. Derle ve yükle:
   ```bash
   idf.py set-target esp32s3
   idf.py build
   idf.py -p COM8 -b 115200 flash
   ```

> **İpucu:** Yükleme 460800 baud'da kopuyorsa `-b 115200` kullan (kablo kalitesine bağlı).

## Dosyalar ve yapılan değişiklikler

| Dosya | Durum | Ne yapıldı |
|---|---|---|
| `main/display/face_engine.h/.cc` | **yeni** | Yüz motoru: göz/kaş/ağız animasyonu, 21 duygu, uyku modu, dudak senkronu |
| `main/display/oled_display.h/.cc` | değiştirildi | Yüz arayüzü + klasik durum ekranı, ikisi arasında geçiş, duygu yönlendirme |
| `main/boards/bread-compact-wifi/config.h` | değiştirildi | Pin haritası (aşağıdaki tablo), dahili LED GPIO21 |
| `main/boards/bread-compact-wifi/compact_wifi_board.cc` | değiştirildi | 4 MCP aracı: `face.sleep`, `face.wake_up`, `screen.show_status`, `screen.show_face` |
| `main/audio/audio_service.cc` | değiştirildi | Hoparlöre giden PCM'den yüz ağzını süren kanca (`FaceOnAudioOutput`) |
| `main/application.cc` | değiştirildi | Uyandırma kelimesi algılanınca uyuyan yüzü uyandırma |
| `main/CMakeLists.txt` | değiştirildi | `display/face_engine.cc` kaynak listesine eklendi |
| `sdkconfig.iva` | yapılandırma | Türkçe dil, 4MB flash + 4MB bölüm planı, quad PSRAM, Jarvis + Computer |

## Pin haritası (ESP32-S3 Zero)

| Parça | Bacak | GPIO |
|---|---|---|
| Mikrofon (INMP441) | SD / WS / SCK | 6 / 7 / 8 |
| Amfi (MAX98357A) | DIN / BCLK / LRC | 12 / 11 / 10 |
| Amfi GAIN | — | GND'ye bağlı |
| OLED (SSD1306) | SDA / SCL | 4 / 3 |
| Dahili RGB LED | — | 21 |

Farklı kablolama kullanıyorsan `config.h` içindeki tanımları değiştirmen yeterli.

## Kritik sdkconfig ayarları

4MB flash'lı ESP32-S3 Zero için bunlar **şart** (yanlışsa cihaz açılmaz veya sığmaz):

```
CONFIG_ESPTOOLPY_FLASHSIZE="4MB"
CONFIG_PARTITION_TABLE_CUSTOM_FILENAME="partitions/v2/4m.csv"
CONFIG_SPIRAM_MODE_QUAD=y          # octal seçilirse açılışta sürekli resetlenir
CONFIG_LANGUAGE_TR_TR=y
CONFIG_OLED_SSD1306_128X64=y
CONFIG_SR_WN_WN9_JARVIS_TTS=y
CONFIG_SR_WN_WN9_COMPUTER_TTS=y
```

> **Dikkat:** Uyandırma kelimesi değiştirildiğinde mutlaka `idf.py build` çalıştır.
> Sadece `flash` çalıştırırsan model paketi (`generated_assets.bin`) güncellenmez ve
> cihaz eski kelimeyle çalışmaya devam eder.

## Yüz motoru nasıl çalışır?

- **Durumlar:** Bekleme (gezinen bakış, göz kırpma) → Dinleme (gözler büyür) →
  Konuşma (ses gücüne göre ağız) → Uyku (kapalı gözler, nefes alma)
- **Duygular:** Sunucudan gelen duygu etiketi 10 yüz ifadesine eşlenir; 12 saniye sonra
  doğal ifadeye döner
- **Çizim mantığı:** Ekranda yalnızca göz/ağız yanar (arka plan sönük) — güç tüketimi düşer
- **Ayar noktaları:** `kEyeBaseW/H`, `kEyeCenterX/Y` (boyut/konum), `Update()` içindeki
  `rand() % 75` (göz kırpma sıklığı), `ComputeTargets()` içindeki ağız katsayıları
