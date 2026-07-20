# Server — kendi sunucun (opsiyonel)

[xiaozhi-esp32-server](https://github.com/xinnan-tech/xiaozhi-esp32-server) tabanlı yerel sunucu.
Türkçe ses tanıma, Türkçe konuşma sesi ve kendi müzik arşivin için.

**Neden gerekli?** Sunucunun varsayılan yerel ses tanıma motoru (SenseVoiceSmall) yalnızca
Çince, Kantonca, İngilizce, Japonca ve Korece destekler — **Türkçe yok**. Bu yüzden ses tanıma
Groq üzerinden Whisper'a yönlendirilir.

## Kurulum

1. Docker Desktop kur ve çalıştır
2. Ücretsiz [Groq API anahtarı](https://console.groq.com/keys) al
3. Yapılandırmayı hazırla:
   ```bash
   mkdir data
   copy config.example.yaml data\.config.yaml
   copy mcp_server_settings.example.json data\.mcp_server_settings.json
   ```
4. `data\.config.yaml` içinde şunları düzenle:
   - `GROQ_API_ANAHTARIN` yazan **iki yeri** kendi anahtarınla değiştir
   - `websocket:` satırındaki `SENIN_YEREL_IP` yerine PC'nin yerel IP'sini yaz (`ipconfig`)
5. Başlat:
   ```bash
   docker compose up -d
   docker logs iva-server --tail 30
   ```

Kayıtlarda şunları görmelisin: `asr成功 GroqASR`, `llm成功 GroqLLM`, `vad成功 SileroVAD`.

## Cihazı bu sunucuya yönlendirmek

Firmware'de tek satır:

```
CONFIG_OTA_URL="http://SENIN_YEREL_IP:8003/xiaozhi/ota/"
```

Sonra `idf.py build` + `flash`. Resmî sunucuya dönmek için:
`https://api.tenclass.net/xiaozhi/ota/`

## Testler

Cihaza hiç dokunmadan Türkçe zincirini sınar (TTS → ASR → LLM):

```bash
copy tests\test_turkish.py data\
docker exec iva-server python /opt/xiaozhi-esp32-server/data/test_turkish.py
```

Araçların (bridge) sunucudan görünüp görünmediğini sınar:

```bash
copy tests\test_mcp.py data\
docker exec iva-server python /opt/xiaozhi-esp32-server/data/test_mcp.py
```

## Müzik

`music/` klasörüne mp3 at. "Sanatçı - Şarkı.mp3" biçiminde adlandırırsan İva şarkıyı adıyla
bulur. Yeni dosyalar en geç 5 dakikada listeye girer (`refresh_time: 300`).

## Notlar

- `auth.enabled: false` — ev ağında pratik, ama ağını paylaşıyorsan açmayı düşün
- Sunucu PC'de çalışır; PC kapalıysa cihaz cevap veremez
- MCP araçları için `bridge/start_iva_tools_http.bat` çalışıyor olmalı
  (konteyner `host.docker.internal:8090` adresinden bağlanır)
