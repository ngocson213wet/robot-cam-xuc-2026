
# Robot Cảm Xúc - NCKH 2026

Hệ thống robot tương tác nhận diện cảm xúc khuôn mặt, phản hồi giọng nói, hiệu ứng biểu cảm màn hình và âm thanh chạy trên Raspberry Pi.

## Cấu trúc thư mục

```text
robot-cam-xuc-2026/
├── main.py              # Chương trình chính điều phối hoạt động của robot
├── emotion.py           # Xử lý nhận diện và phân tích cảm xúc
├── face.py              # Hiển thị biểu cảm khuôn mặt lên màn hình
├── anh.py               # Quản lý và xử lý tài nguyên hình ảnh
├── sound.py             # Điều khiển phát nhạc nền và hiệu ứng âm thanh
├── online.py            # Xử lý kết nối mạng và tương tác trực tuyến
├── thoai_excited.py     # Kịch bản hội thoại trạng thái hào hứng
├── anh1/                # Bộ hình ảnh biểu cảm khuôn mặt
├── nhac/                # Kho âm thanh theo từng trạng thái (excited, normal, sadness)
├── thoai_excited/       # File âm thanh hội thoại trạng thái excited
├── chao.mp3             # Âm thanh lời chào khởi động
├── dandar.mp3           # Âm thanh hiệu ứng
├── requirements.txt     # Danh sách thư viện Python cần thiết
├── setup.sh             # Script tự động cài đặt môi trường và systemd service
└── .service             # Cấu hình mẫu cho dịch vụ chạy tự động
Bước 1: Cập nhật và cài đặt git cho Raspberry Pi
sudo apt update && sudo apt install git -y
Bước 2: Clone đúng đường dẫn kho mã nguồn và mở thư mục dự án
git clone https://github.com/ngocson213wet/robot-cam-xuc-2026.git
cd robot-cam-xuc-2026
Bước 3: Chạy tập lệnh cài đặt môi trường (nếu chưa thiết lập venv và thư viện trên Pi)
Trong cây thư mục dự án của bạn đã có sẵn tệp setup.sh, bạn có thể cấp quyền và chạy tự động:
chmod +x setup.sh
./setup.sh

* Vận hành & Quản lý dịch vụ
source venv/bin/activate
python main.py
*Quản lý chế độ tự chạy cùng hệ thống (systemd):
sudo systemctl start robot.service     # Bật robot ngay lập tức
sudo systemctl status robot.service    # Kiểm tra trạng thái hoạt động
sudo systemctl restart robot.service   # Khởi động lại sau khi sửa code
sudo systemctl stop robot.service      # Dừng chạy ngầm
journalctl -u robot.service -f         # Xem log thời gian thực