# Sıfırdan kurulum (yeni/eski bilgisayarda)

Amaç: repoyu klonla, tek komut çalıştır, sistem ayağa kalksın.

## 0. Gereksinimler

| | Neden | Not |
|---|---|---|
| Python 3.10+ | İva'nın araçları | [python.org](https://www.python.org/downloads/) — kurulumda "Add to PATH" işaretle |
| Git | Repoyu çekmek | |
| Docker Desktop | *sadece* kendi sunucunu kullanacaksan | Eski/zayıf makinede atlayabilirsin |
| ESP-IDF v5.5.x | *sadece* firmware derleyeceksen | Cihaz zaten yüklüyse gerekmez |

## 1. Repoyu al

```powershell
git clone https://github.com/Talha-Dogan/iva_desk_pet.git
cd iva_desk_pet
```

## 2. Tek komutla kur

```powershell
powershell -ExecutionPolicy Bypass -File setup.ps1
```

Bu komut şunları yapar:

1. Python'u bulur, `bridge\venv` sanal ortamını kurar
2. Bağımlılıkları yükler (`mcp`, `websockets`, `requests`)
3. `bridge\.env.example` → `bridge\.env` kopyalar
4. Windows açılışına otomatik başlatma kısayolu ekler

Kendi sunucunu da kuracaksan:

```powershell
powershell -ExecutionPolicy Bypass -File setup.ps1 -WithServer -Mode http
```

## 3. Anahtarları doldur

`bridge\.env` dosyasını aç:

```
MCP_ENDPOINT=        xiaozhi.me -> Extensions -> MCP Endpoint (kopyala düğmesi)
TELEGRAM_BOT_TOKEN=  Telegram'da @BotFather -> /newbot
TELEGRAM_CHAT_ID=    aşağıdaki nota bak
DIGEST_HOUR=21       günlük özet saati
```

**Sohbet kimliğini bulmak:** botu grubuna ekle → gruba `/start@botadi` yaz →
tarayıcıda `https://api.telegram.org/bot<TOKEN>/getUpdates` aç → `"chat":{"id":-100...}`
değerini kopyala. (Bot gizlilik modu açık olduğu için normal mesajları görmez, `/start` şart.)

## 4. Başlat ve doğrula

```powershell
bridge\start_iva_bridge.bat
```

Kontrol listesi:

- [ ] Pencerede/`bridge\logs\bridge.log` içinde **"Baglanti kuruldu!"** yazıyor
- [ ] xiaozhi.me → Extensions → MCP Endpoint durumu **"Connected"**
- [ ] Cihaza "not al: kurulum tamam" dediğinde `bridge\data\notes\` altında dosya oluşuyor
- [ ] "notları Telegram'a gönder" dediğinde mesaj geliyor

## 5. Cihaz tarafı

Cihaz zaten programlıysa hiçbir şey yapmana gerek yok — sadece aynı WiFi'ye bağlanması yeter.
Yeniden derleyecek/yükleyecekseniz: [firmware/README.md](../firmware/README.md)

## Otomatik başlatma

`setup.ps1` bunu zaten kurar. Elle yönetmek istersen:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_autostart.ps1 -Mode both
powershell -ExecutionPolicy Bypass -File scripts\uninstall_autostart.ps1
```

Kısayollar `shell:startup` klasörüne eklenir ve servisleri **gizli pencerede** başlatır;
kayıtlar `bridge\logs\` altına yazılır.

Kendi sunucunu kullanıyorsan Docker Desktop → Settings → General →
**"Start Docker Desktop when you sign in"** seçeneğini de aç. Konteyner `restart: always`
ayarlı olduğu için Docker açılınca kendiliğinden kalkar.

## Sorun giderme

| Belirti | Bak |
|---|---|
| Araçlar çalışmıyor, İva "yapamıyorum" diyor | `bridge\logs\bridge.log` — bağlantı kurulmuş mu? |
| Konsolda "Not Connected" | `.env` içindeki `MCP_ENDPOINT` boş veya süresi dolmuş olabilir |
| Telegram'a mesaj gitmiyor | Token/chat id yanlış; `getMe` ile token'ı sına |
| Kurulumdan sonra hiçbir şey başlamıyor | Görev yöneticisinde `python.exe` var mı? Yoksa `.bat`'ı elle çalıştırıp hatayı gör |
| PC uykuya girince İva sessizleşiyor | Beklenen davranış; güç ayarlarından uykuyu kapatabilirsin |
