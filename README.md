# 📺 PiTV

Een standalone display-app voor Raspberry Pi met 7" touchscreen. Toont klok, weer, crypto en pushed afbeeldingen. Draait volledig lokaal — geen Home Assistant vereist.

---

## Apps

| App | Beschrijving |
|-----|-------------|
| 🕐 **Klok** | Grote digitale klok met datum en weeknummer |
| 🌤️ **Weer** | Actueel weer + 3-daagse voorspelling (Open-Meteo, gratis) |
| ₿ **Crypto** | BTC en ETH prijs + 24u % verandering (CoinGecko, gratis) |
| 🖼️ **Foto** | Fullscreen afbeeldingen, gepushed via API |

Navigeren: tik op linker/rechter rand of swipe. Auto-rotate elke 30 seconden (pauzeert tijdens foto).

---

## Installatie (Raspberry Pi OS)

### 1. Clone de repo
```bash
cd ~
git clone https://github.com/captain-nemo/pitv.git
cd pitv
```

### 2. Run de installer
```bash
chmod +x install.sh
./install.sh
```

Dit doet:
- Python venv aanmaken + dependencies installeren
- systemd service installeren en starten
- Chromium kiosk autostart instellen

### 3. Reboot
```bash
sudo reboot
```

Na reboot: server draait op poort 8765, Chromium opent automatisch in kiosk-modus.

---

## Handmatige installatie (stap voor stap)

```bash
# Dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Server starten
./start.sh
# of: uvicorn server:app --host 0.0.0.0 --port 8765

# Browser openen (op de Pi zelf)
chromium-browser --kiosk http://localhost:8765
```

---

## API

### Afbeelding pushen
```bash
# Via file upload
curl -X POST http://pitv.local:8765/push/image -F "file=@/pad/naar/afbeelding.png"

# Via lokaal pad (server-side)
curl -X POST http://pitv.local:8765/push/image -F "path=/pad/naar/afbeelding.png"
```

### App wisselen
```bash
curl -X POST http://pitv.local:8765/push/app \
  -H "Content-Type: application/json" \
  -d '{"app": "clock"}'
# apps: clock | weather | crypto | photo
```

### Status opvragen
```bash
curl http://pitv.local:8765/status
```

---

## Locatie aanpassen (weer)

Pas de coördinaten aan in `static/index.html`:
```js
const WEATHER_LAT = 51.37, WEATHER_LON = 6.17;  // Venlo, NL
```

---

## Systemd service

```bash
sudo systemctl status pitv    # status
sudo systemctl restart pitv   # herstart
sudo journalctl -u pitv -f    # logs
```

---

## Tips

- **mDNS:** Stel hostnaam in als `pitv` via `sudo raspi-config` → System Options → Hostname, dan bereikbaar via `pitv.local`
- **Scherm altijd aan:** Voeg toe aan `/etc/lightdm/lightdm.conf` onder `[SeatDefaults]`:
  ```
  xserver-command=X -s 0 dpms
  ```
- **Automatisch updates:** `git pull && sudo systemctl restart pitv`

---

## Requirements

- Raspberry Pi (3B+ of nieuwer aanbevolen)
- Raspberry Pi OS met desktop (Bookworm)
- Python 3.9+
- Chromium (standaard aanwezig op RPi OS)
- Internetverbinding voor weer- en crypto-data
