# Donanım ve kablolama

## Parça listesi

| Parça | Model | Yaklaşık rol |
|---|---|---|
| Geliştirme kartı | ESP32-S3 Zero | 4MB flash, 2MB quad PSRAM |
| Mikrofon | INMP441 | I2S dijital mikrofon |
| Amfi | MAX98357A | I2S dijital amfi (D sınıfı) |
| Hoparlör | 4Ω 3W (veya benzeri) | Amfiye bağlanır |
| Ekran | SSD1306 OLED 128x64 | I2C |
| Breadboard + jumper | — | Prototip için |

## Kablolama

### Mikrofon (INMP441)

| INMP441 | ESP32-S3 |
|---|---|
| VDD | 3V3 |
| GND | GND |
| SD | GPIO 6 |
| WS | GPIO 7 |
| SCK | GPIO 8 |
| L/R | GND |

### Amfi (MAX98357A)

| MAX98357A | ESP32-S3 |
|---|---|
| VIN | 5V (veya 3V3) |
| GND | GND |
| DIN | GPIO 12 |
| BCLK | GPIO 11 |
| LRC | GPIO 10 |
| GAIN | GND (sabit kazanç) |

### OLED (SSD1306, I2C)

| OLED | ESP32-S3 |
|---|---|
| VCC | 3V3 |
| GND | GND |
| SDA | GPIO 4 |
| SCL | GPIO 3 |

> Modül üzerindeki pin sırası markaya göre değişir — **kartın üzerindeki yazıya göre** bağla.

## Sık karşılaşılan sorunlar

| Belirti | Olası sebep |
|---|---|
| Ekran hiç yanmıyor | VCC/GND ters, SDA-SCL yer değişmiş, jumper temassız |
| Kayıtta `i2c transaction failed` | Ekran hattı fiziksel olarak cevap vermiyor (kablo) |
| Cihaz açılışta sürekli resetleniyor | PSRAM modu yanlış (quad olmalı) |
| Ses yok | Amfi VIN bağlı değil, DIN/BCLK/LRC karışmış |
| Yükleme yarıda kopuyor | USB kablosu zayıf → `-b 115200` ile dene |
| COM portu görünmüyor | Sadece şarj kablosu kullanılmış (veri hattı yok) |

## Güç notları

- Cihaz USB'den beslenir; pil yönetimi bu sürümde yok
- Yüz çizimi yalnızca göz/ağız piksellerini yakar → OLED tüketimi ve yanma riski düşer
- Uyku modunda ekran içeriği minimuma iner
