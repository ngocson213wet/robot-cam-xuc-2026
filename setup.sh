#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURRENT_USER="$(whoami)"
SERVICE_NAME="robot.service"

echo "=== 1. Cập nhật hệ thống & cài đặt thư viện nền (Audio/OpenCV) ==="
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv python3-dev \
    libsdl2-dev libsdl2-mixer-2.0-0 libportaudio2 ffmpeg libgl1

echo "=== 2. Kiểm tra & mở rộng Swap (chống tràn RAM 4GB khi cài/chạy AI) ==="
SWAP_SIZE=$(free -m | awk '/^Swap:/ {print $2}')
if [ "$SWAP_SIZE" -lt 2048 ]; then
    echo "Đang mở rộng Swap lên 2048MB..."
    if [ -f /etc/dphys-swapfile ]; then
        sudo dphys-swapfile swapoff || true
        sudo sed -i 's/^CONF_SWAPSIZE=.*/CONF_SWAPSIZE=2048/' /etc/dphys-swapfile
        sudo dphys-swapfile setup
        sudo dphys-swapfile swapon
    fi
fi

echo "=== 3. Tạo môi trường ảo venv & cài đặt requirements.txt ==="
cd "$PROJECT_DIR"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install --no-cache-dir -r requirements.txt
else
    echo "Cảnh báo: Không tìm thấy file requirements.txt!"
fi

echo "=== 4. Kiểm tra file cấu hình .env ==="
if [ ! -f ".env" ]; then
    cat <<EOF > .env
# Điền API Key và cấu hình của bạn vào đây
GEMINI_API_KEY=your_api_key_here
EOF
    echo "Đã tạo file .env mẫu. Hãy mở file .env để điền API Key trước khi chạy!"
fi

echo "=== 5. Cài đặt dịch vụ tự khởi động ($SERVICE_NAME) ==="
sudo bash -c "cat <<EOF > /etc/systemd/system/$SERVICE_NAME
[Unit]
Description=Robot Cam Xuc NCKH 2026
After=network-online.target sound.target
Wants=network-online.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$PROJECT_DIR
EnvironmentFile=-$PROJECT_DIR/.env
ExecStart=$PROJECT_DIR/venv/bin/python$PROJECT_DIR/main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF"

sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"

echo "=== Cài đặt hoàn tất! ==="
echo "- Chạy thử thủ công: source venv/bin/activate && python main.py"
echo "- Khởi động dịch vụ nền: sudo systemctl start $SERVICE_NAME"