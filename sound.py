import logging
import os
import subprocess

log = logging.getLogger("robot.sound")


def chay_nhac(file_name, dung=None):
    """Phát 1 file mp3 bằng mpg123 và chờ phát xong.

    dung: threading.Event (tuỳ chọn). Nếu được set trong lúc đang phát thì tắt nhạc ngay.
    Trả về True nếu phát hết, False nếu bị ngắt / thiếu file / lỗi. Không ném exception.
    """
    full_path = os.path.abspath(file_name)
    if not os.path.exists(full_path):
        log.warning("không thấy file nhạc: %s", full_path)
        return False

    log.info("đã chạy bài %s", full_path)
    try:
        p = subprocess.Popen(["mpg123", "-q", full_path])
    except OSError as e:                      # chưa cài mpg123...
        log.error("không chạy được mpg123: %s", e)
        return False

    try:
        while p.poll() is None:
            if dung is not None and dung.wait(0.1):   # bị yêu cầu dừng
                p.terminate()
                try:
                    p.wait(2)
                except subprocess.TimeoutExpired:
                    p.kill()
                    p.wait()
                return False
            elif dung is None:
                try:
                    p.wait(0.1)
                except subprocess.TimeoutExpired:
                    pass
        return p.returncode == 0
    finally:
        if p.poll() is None:                  # chắc chắn không để mpg123 mồ côi
            p.kill()
            p.wait()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    chay_nhac("chao.mp3")
    print("đã chạy bài hát")