#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# 0. Kiểm tra đủ file trước (thiếu thì dừng, không bật service hỏng)
THIEU=0
for f in main.py online.py sound.py emotion.py anh.py face.py chao.mp3 dandar.mp3 nhac/normal2.mp3 \
         "anh1/Group 48.png" "anh1/Group 46.png" "anh1/Group 73.png" "anh1/Group 65.png"; do
    [ -e "$f" ] || { echo "!! THIẾU FILE: $f"; THIEU=1; }
done
[ "$THIEU" = 0 ] || { echo "Chép đủ file rồi chạy lại."; exit 1; }

# 1. API key
if [ -f .env ] && grep -q '^GEMINI_API_KEY=.\+' .env; then
    echo ">> .env đã có GEMINI_API_KEY, giữ nguyên"
else
    KEY=""
    while [ -z "$KEY" ]; do
        read -rsp "Nhập GEMINI_API_KEY (dán vào, màn hình sẽ không hiện chữ): " KEY
        echo
    done
    touch .env
    sed -i '/^GEMINI_API_KEY=/d' .env
    printf 'GEMINI_API_KEY=%s\n' "$KEY" >> .env
    chmod 600 .env
    echo ">> Đã lưu vào .env"
fi

# 2. Gói hệ thống
sudo apt update
sudo apt install -y python3-venv python3-psutil python3-pygame python3-numpy \
                    alsa-utils mpg123 v4l-utils

# 3. Quyền truy cập loa, camera, màn hình
sudo usermod -aG audio,video,render "$USER"

# 4. venv + gói pip
python3 -m venv --system-site-packages venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 5. Kiểm tra nhanh
python - <<'PY'
import cv2, pygame, psutil, numpy
from google import genai
print(">> import OK, OpenCV", cv2.__version__, "CascadeClassifier:", hasattr(cv2, "CascadeClassifier"))
PY
ls /dev/video* >/dev/null 2>&1 && echo ">> Thấy camera: $(ls /dev/video* | tr '\n' ' ')" \
                               || echo "!! CHƯA thấy camera (/dev/video*)"
aplay -l 2>/dev/null | grep -q card && echo ">> Thấy thiết bị âm thanh" \
                                    || echo "!! CHƯA thấy thiết bị âm thanh"

# 6. Service tự chạy khi bật nguồn
sudo tee /etc/systemd/system/robot.service > /dev/null <<UNIT
[Unit]
Description=Robot
After=network-online.target sound.target
Wants=network-online.target

[Service]
User=$USER
SupplementaryGroups=audio video render
WorkingDirectory=$DIR
EnvironmentFile=$DIR/.env
ExecStart=$DIR/venv/bin/python main.py
Restart=on-failure
RestartSec=5
TimeoutStopSec=60

[Install]
WantedBy=multi-user.target
UNIT
sudo systemctl daemon-reload
sudo systemctl enable --now robot

echo ">> Xong. Xem log: journalctl -u robot -f"
echo ">> Nên chạy 'sudo reboot' 1 lần để quyền audio/video có hiệu lực hoàn toàn."