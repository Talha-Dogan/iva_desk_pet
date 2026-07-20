# Mimari

## Genel akış

```
 "Jarvis"          ses                    metin              cevap             ses
   ▼                │                       │                  │                │
┌──────────────┐    │   ┌──────────────┐    │   ┌──────────┐    │   ┌────────┐   │
│ Uyandırma    │────┼──►│ ASR          │────┼──►│ LLM      │────┼──►│ TTS    │───┘
│ (cihazda)    │    │   │ (sunucuda)   │    │   │(sunucuda)│    │   │(sunucu)│
└──────────────┘    │   └──────────────┘    │   └────┬─────┘    │   └────────┘
                    │                       │        │ araç çağrısı
                    │                       │        ▼
                    │                       │   ┌──────────────┐
                    │                       │   │ MCP araçları │ (senin PC'nde)
                    │                       │   │ not/Telegram │
                    │                       │   └──────────────┘
```

**Cihazda çalışan tek yapay zekâ parçası uyandırma kelimesidir** (offline, ~200 ms).
Geri kalan her şey sunucudadır; bu yüzden cihaz internetsiz sohbet edemez.

## Firmware katmanları

```
application.cc          durum makinesi (bekleme/dinleme/konuşma), olay döngüsü
├── audio_service.cc    mikrofon → Opus → sunucu, sunucu → hoparlör
│   └── FaceOnAudioOutput()   ← dudak senkronu kancası
├── display/
│   ├── oled_display.cc  iki arayüz: yüz ekranı + klasik durum ekranı
│   └── face_engine.cc   yüz animasyonu (durumlar, duygular, uyku)
└── boards/bread-compact-wifi/
    ├── config.h              pin haritası
    └── compact_wifi_board.cc kart kurulumu + cihaz üstü MCP araçları
```

### Yüz motoru mantığı

Her 40 ms'de bir çalışan bir döngü:

1. **Hedefleri hesapla** (`ComputeTargets`) — duruma göre göz/ağız/bakış hedefleri
2. **Duyguyu uygula** (`ApplyEmotion`) — hedeflerin üzerine ifade değişiklikleri
3. **Çiz** (`ApplyGeometry`) — hedeflere doğru yumuşak geçiş (interpolasyon)

Bu üç aşamalı yapı sayesinde her şey akıcı görünür; ani sıçrama olmaz.

**Görsel numaralar:**
- *Squash & stretch* — göz kapanırken hafifçe genişler (hacim hissi)
- *Merak* — bakılan yöndeki göz büyür (kafa çevirme izlenimi)
- *Yanak/kaş oyma* — sönük renkli dikdörtgenler gözün altını (mutlu ^^) veya
  üst köşelerini (kızgın/üzgün) örterek ifade yaratır
- *Çift kırpma* — ara sıra art arda iki kırpma, tek düzeliği kırar

## MCP araç zinciri

```
LLM "not al" der
   │
   ▼
sunucu → MCP protokolü → köprü (senin PC'n) → tools.py fonksiyonu → dosya/Telegram
```

İki taşıma yöntemi:

| Sunucu | Taşıma | Dosya |
|---|---|---|
| Resmî (xiaozhi.me) | WebSocket (dışa bağlanır) | `mcp_pipe.py` |
| Kendi sunucun | HTTP streamable (konteyner bağlanır) | `tools_http.py` |

İkisi de aynı `tools.py` araçlarını kullanır; sadece paketleme farklıdır.

## Tasarım kararları

**Neden cihazda değil sunucuda zekâ?** ESP32-S3'te 2MB PSRAM var; modern bir dil modeli
sığmaz. Cihaz "kulak + yüz + hoparlör" olarak en iyi işi yapar.

**Neden uyandırma kelimesi cihazda?** Sürekli ses akışı hem gizlilik sorunudur hem bant
genişliği. Cihaz yalnızca kelimeyi duyunca bağlanır.

**Neden ağız sese bağlı, mesaja değil?** Sunucu "konuşmaya başlıyorum" mesajını sesten
yaklaşık bir saniye önce gönderiyor; mesajla tetiklenen ağız sessizlikte oynuyordu.
Hoparlöre giden PCM verisinin anlık gücü kullanılınca senkron doğal hale geldi.

**Neden yalnızca göz/ağız yanıyor?** Bu OLED'de siyah = yanan piksel. Yüz "siyah zemin"
çizilirse ekranın tamamı yanar. Ters çevrilince yanan piksel oranı ~%90'dan ~%10'a düştü.

**Neden 4MB kartta OTA yok?** Bölüm planında iki uygulama alanı + varlık alanı sığmıyor.
16MB kartta OTA, özel uyandırma kelimesi ve zengin görseller birlikte mümkün.
