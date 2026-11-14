"""Camera: kiểm tra camera có chạy không, rồi xác định có người hay không."""
import logging
import os
import time 

import cv2

log = logging.getLogger("robot.nguoi")

CAMERA_INDEX = int(os.environ.get("CAMERA_INDEX", "0"))

# Bộ dò mặt có sẵn của OpenCV (chạy trên máy, không cần mạng)
if not hasattr(cv2, "CascadeClassifier"):    # OpenCV 5.x đã bỏ CascadeClassifier khỏi module chính
    raise RuntimeError(f"OpenCV {cv2.__version__} không có CascadeClassifier -> pip install 'opencv-python-headless<5'")
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
if face_cascade.empty():
    raise RuntimeError("Không nạp được haarcascade_frontalface_default.xml (kiểm tra cài đặt opencv)")


def kiem_tra_nguoi(index=CAMERA_INDEX, so_khung=5):
    """Bước 1: camera có chạy không. Bước 2: trong ảnh có người (có mặt) không.

    Trả về (camera_ok, co_nguoi):
        (False, False)  camera lỗi, chưa thể biết có người hay không
        (True,  False)  camera chạy tốt, không thấy người
        (True,  True)   camera chạy tốt, có người
    Luôn nhả camera trước khi trả về và không ném exception.
    """
    cap = None
    try:
        cap = cv2.VideoCapture(index)
        if not cap.isOpened():
            log.error("không mở được camera index %s", index)
            return False, False

        # Bước 1: đọc thử vài khung, lấy được 1 khung hợp lệ là camera chạy
        khung = None
        for _ in range(so_khung):
            ok, f = cap.read()
            if ok and f is not None:
                khung = f
        if khung is None:
            log.error("camera %s mở được nhưng không đọc được khung hình", index)
            return False, False
        log.info("camera %s chạy tốt", index)

        # Bước 2: dò mặt trên khung vừa đọc
        gray = cv2.cvtColor(khung, cv2.COLOR_BGR2GRAY)
        mat = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))
        co_nguoi = len(mat) > 0
        log.info("có người" if co_nguoi else "không thấy người")
        return True, co_nguoi
    except Exception:
        log.exception("lỗi khi kiểm tra camera %s", index)
        return False, False
    finally:
        if cap is not None:
            cap.release()


def xac_nhan_co_nguoi(index=CAMERA_INDEX, so_khung=5):
    """Trả về 1 nếu camera chạy VÀ có người, còn lại trả về 0."""
    camera_ok, co_nguoi = kiem_tra_nguoi(index, so_khung)
    return 1 if (camera_ok and co_nguoi) else 0

def anh_duyet(index=CAMERA_INDEX, so_anh=5, thoi_gian=5):
    """Lấy `so_anh` ảnh trong `thoi_gian` giây (mặc định 5 ảnh / 5 giây = 1 ảnh mỗi giây).
 
    Trả về list các ảnh (mảng numpy BGR). Camera lỗi thì trả về list rỗng [].
    Nếu chỉ lấy được một phần ảnh thì trả về phần đã lấy được.
    Luôn nhả camera trước khi trả về và không ném exception.
    """
    anh = []
    cap = None
    try:
        cap = cv2.VideoCapture(index)
        if not cap.isOpened():
            log.error("không mở được camera index %s", index)
            return []
 
        for _ in range(5):          # bỏ vài khung đầu vì camera mới mở thường tối/chưa ổn
            cap.read()
 
        buoc = thoi_gian / so_anh   # khoảng cách giữa 2 ảnh (giây)
        bat_dau = time.monotonic()
        han_chot = bat_dau + thoi_gian + 3   # đề phòng camera đọc lỗi mãi thì không bị kẹt
        khung = None
        while len(anh) < so_anh and time.monotonic() < han_chot:
            # cứ đọc liên tục để luôn có khung mới nhất (tránh lấy phải ảnh cũ trong bộ đệm)
            ok, f = cap.read()
            if ok and f is not None:
                khung = f
            # tới mốc giây thứ 1, 2, 3... thì giữ lại khung mới nhất
            if khung is not None and time.monotonic() - bat_dau >= (len(anh) + 1) * buoc:
                anh.append(khung)
                log.info("đã lấy ảnh %d/%d", len(anh), so_anh)
 
        if len(anh) < so_anh:
            log.warning("chỉ lấy được %d/%d ảnh", len(anh), so_anh)
        return anh
    except Exception:
        log.exception("lỗi khi lấy ảnh từ camera %s", index)
        return []
    finally:
        if cap is not None:
            cap.release()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    ket_qua = xac_nhan_co_nguoi()
    print(f"\n--- KẾT QUẢ TRẢ VỀ: {ket_qua} ---")