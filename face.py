import os
import sys
import time
import threading
import pygame

# --- 1. CẤU HÌNH ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

EMOTION_MAP = {
    100: os.path.join(BASE_DIR, "anh1", "Group 48.png"),  # Normal
    200: os.path.join(BASE_DIR, "anh1", "Group 46.png"),  # Excited
    300: os.path.join(BASE_DIR, "anh1", "Group 73.png"),  # Sadness
    400: os.path.join(BASE_DIR, "anh1", "Group 65.png"),  # Angry
}

# Tên -> ID (thêm tên khác nếu emotion.py trả về chuỗi khác)
NAME_TO_ID = {
    "normal": 100,
    "excited": 200,
    "sadness": 300,
    "angry": 400,
    # tiếng Việt (tùy chọn)
    "bình thường": 100,
    "vui": 200,
    "buồn": 300,
    "tức giận": 400,
}

DEFAULT_EMOTION = 100
BG_COLOR = (142, 226, 247)
FPS = 30
WINDOW_SIZE = (800, 480)          # kích thước cửa sổ khi test trên Mac

# --- 2. TRẠNG THÁI DÙNG CHUNG ---
_lock = threading.Lock()
_state = {"id": DEFAULT_EMOTION, "end": 0.0}
_stop_event = threading.Event()
_thread = None


# --- 3. HÀM CHÍNH CHO FILE KHÁC GỌI: play_emotion(cảm xúc, thời gian) ---
def play_emotion(emotion, duration=0):
    """
    :param emotion: ID (100/200/300/400) hoặc tên ("normal", "excited", ...)
    :param duration: số giây hiển thị rồi tự về Normal. 0 = giữ mãi.
    """
    if isinstance(emotion, str):
        key = emotion.strip().lower()
        eid = NAME_TO_ID.get(key)
        if eid is None and key.isdigit():
            eid = int(key)
    else:
        eid = emotion

    if eid not in EMOTION_MAP:
        raise ValueError(f"Cảm xúc không hợp lệ: {emotion}")

    start()  # tự bật màn hình nếu chưa chạy
    with _lock:
        _state["id"] = eid
        _state["end"] = time.monotonic() + duration if duration > 0 else 0.0


# --- 4. VÒNG LẶP HIỂN THỊ ---
def _load_images(sw, sh):
    images = {}
    for eid, path in EMOTION_MAP.items():
        if not os.path.exists(path):
            print(f"[WARN] Không tìm thấy ảnh: {path}")
            continue
        img = pygame.image.load(path).convert_alpha()
        w, h = img.get_size()
        # Thu nhỏ (giữ tỉ lệ) nếu ảnh lớn hơn màn hình
        if w > sw or h > sh:
            scale = min(sw / w, sh / h)
            img = pygame.transform.smoothscale(img, (int(w * scale), int(h * scale)))
        images[eid] = img
    return images


def _display_loop(windowed=False):
    if not windowed and sys.platform.startswith("linux"):
        os.environ.setdefault("SDL_VIDEODRIVER", "kmsdrm")

    pygame.display.init()   # không dùng pygame.init(): nó chiếm card âm thanh làm mpg123 mất tiếng
    if windowed:
        screen = pygame.display.set_mode(WINDOW_SIZE)
        pygame.display.set_caption("Robot Face")
    else:
        info = pygame.display.Info()
        screen = pygame.display.set_mode(
            (info.current_w, info.current_h), pygame.FULLSCREEN
        )
        pygame.mouse.set_visible(False)
    sw, sh = screen.get_size()

    images = _load_images(sw, sh)
    clock = pygame.time.Clock()

    while not _stop_event.is_set():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                _stop_event.set()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    _stop_event.set()
                elif event.key == pygame.K_1:
                    play_emotion("excited", 2)
                elif event.key == pygame.K_2:
                    play_emotion("sadness", 5)
                elif event.key == pygame.K_3:
                    play_emotion("angry", 3)

        # Hết thời gian -> về Normal
        with _lock:
            if _state["end"] > 0 and time.monotonic() >= _state["end"]:
                _state["id"] = DEFAULT_EMOTION
                _state["end"] = 0.0
            current = _state["id"]

        screen.fill(BG_COLOR)
        img = images.get(current)
        if img:
            screen.blit(img, img.get_rect(center=(sw // 2, sh // 2)))
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


# --- 5. ĐIỀU KHIỂN ---
def start():
    """Bật màn hình ở thread nền (play_emotion tự gọi hàm này)."""
    global _thread
    if _thread and _thread.is_alive():
        return
    _stop_event.clear()
    _thread = threading.Thread(
        target=_display_loop,
        kwargs={"windowed": sys.platform == "darwin"},
        daemon=True,
    )
    _thread.start()


def stop():
    """Tắt màn hình."""
    _stop_event.set()
    if _thread:
        _thread.join()


def run():
    """Chạy chặn ở thread chính (dùng khi chạy trực tiếp file này, ổn định nhất)."""
    _stop_event.clear()
    _display_loop(windowed=(sys.platform == "darwin"))


# --- 6. TEST: python3 face.py ---
if __name__ == "__main__":
    play_emotion("angry", 3)   # đặt trạng thái ban đầu (bật thread nền)
    stop()                     # tắt thread nền để chạy ở thread chính
    play_emotion_state = None
    with _lock:
        _state["id"] = 400
        _state["end"] = time.monotonic() + 3
    run()