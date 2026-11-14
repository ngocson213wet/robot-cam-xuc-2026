
import logging
import os
import threading

import sound

log = logging.getLogger("robot.online")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GREETING = os.path.join(BASE_DIR, "chao.mp3")
GUIDE = os.path.join(BASE_DIR, "dandar.mp3")
IDLE_MUSIC = os.path.join(BASE_DIR, "nhac", "normal2.mp3")
DELAY = 30            # giây chờ giữa lời chào và hướng dẫn
STOP_TIMEOUT = 45     # nhận diện cảm xúc có thể mất tới ~5s chụp + 30s Gemini, không ngắt giữa chừng được


class Online:
    def __init__(self):
        self._dung = threading.Event()
        self._thread = None

    @property
    def dang_chay(self):
        return self._thread is not None and self._thread.is_alive()

    def start(self):
        if self.dang_chay:
            return
        self._dung.clear()
        self._thread = threading.Thread(target=self._chay, name="online", daemon=True)
        self._thread.start()
        log.info("chế độ ONLINE: bắt đầu")

    def stop(self):
        self._dung.set()
        t = self._thread
        if t is not None and t is not threading.current_thread():
            t.join(STOP_TIMEOUT)
            if t.is_alive():
                log.warning("thread online chưa dừng sau %ss", STOP_TIMEOUT)
                return                      # giữ tham chiếu để dang_chay vẫn đúng
        self._thread = None
        log.info("chế độ ONLINE: đã dừng")

    # ---- bên trong ----
    def _lay_cam_xuc(self):
        """Nhận diện cảm xúc 1 lần. None nếu lỗi / không có người."""
        try:
            import emotion                  # import lười: lỗi OpenCV/Gemini không làm sập cả main & chế độ offline
            return emotion.nhan_dien_cam_xuc()
        except Exception:
            log.exception("nhan_dien_cam_xuc")
            return None

    def _chay(self):
        try:
            cam_xuc = self._lay_cam_xuc()
            log.info("--- CẢM XÚC: %s ---", cam_xuc)
            if self._dung.is_set():         # trong lúc chờ Gemini mà đã rớt mạng -> bỏ
                return


            while not self._dung.is_set():
                try:
                    sound.chay_nhac(GREETING, self._dung)
                    if self._dung.wait(DELAY):
                        break
                    sound.chay_nhac(GUIDE, self._dung)
                    sound.chay_nhac(IDLE_MUSIC, self._dung)
                except Exception:
                    log.exception("vòng lặp online")
                    if self._dung.wait(1):  # tránh lặp lỗi quá nhanh
                        break
        except Exception:
            log.exception("thread online thoát vì lỗi")