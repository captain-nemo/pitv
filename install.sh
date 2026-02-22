#!/bin/bash
# PiTV installer for Raspberry Pi OS
set -e

INSTALL_DIR="$(pwd)"
SERVICE_FILE="/etc/systemd/system/pitv.service"

echo "=== PiTV Installer ==="
echo "Install dir: $INSTALL_DIR"

# 1. Python venv + deps
echo "[1/4] Installing Python dependencies..."
python3 -m venv venv
source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo "OK"

# 2. Systemd service
echo "[2/4] Installing systemd service..."
# Update WorkingDirectory and user in service file
CURRENT_USER=$(whoami)
sed -e "s|/home/pi/pitv|$INSTALL_DIR|g" \
    -e "s|User=pi|User=$CURRENT_USER|g" \
    pitv.service | sudo tee "$SERVICE_FILE" > /dev/null
sudo systemctl daemon-reload
sudo systemctl enable pitv
sudo systemctl restart pitv
echo "OK"

# 3. Chromium kiosk autostart
echo "[3/4] Setting up Chromium kiosk autostart..."
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"
cat > "$AUTOSTART_DIR/pitv-kiosk.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=PiTV Kiosk
Exec=bash -c 'sleep 5 && chromium-browser --kiosk --noerrdialogs --disable-infobars --no-first-run --disable-session-crashed-bubble --disable-restore-session-state http://localhost:8765'
X-GNOME-Autostart-enabled=true
EOF
echo "OK"

# 4. Done
echo "[4/4] Done!"
echo ""
echo "PiTV server: sudo systemctl status pitv"
echo "Push image:  curl -X POST http://$(hostname -I | awk '{print $1}'):8765/push/image -F 'file=@/path/to/image.png'"
echo ""
echo "Reboot to start kiosk automatically, or run: ./start.sh"
