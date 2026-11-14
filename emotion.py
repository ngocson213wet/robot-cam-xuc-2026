"""Lấy ảnh từ camera (anh.py) -> Gemini phân loại cảm xúc -> xoá ảnh khỏi bộ nhớ.

Kết quả trả về là 1 trong 4 nhãn: "excited", "sadness", "normal", "angry".
"""
import logging
import os

import cv2
from google import genai
from google.genai import types

import anh

log = logging.getLogger("robot.emotion")

MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")   # đổi bằng biến môi trường, không cần sửa code
TIMEOUT_S = 30                                                    # chờ Gemini tối đa 30 giây

NHAN = ("excited", "sadness", "normal", "angry")                  # 4 nhãn của bài toán

CAU_HOI = (
    "Đây là 5 ảnh liên tiếp chụp trong 5 giây của cùng một người. "
    "Hãy xác định cảm xúc chủ đạo trên khuôn mặt người đó, chọn ĐÚNG MỘT trong 4 nhãn sau: "
    "excited (hào hứng, vui vẻ), sadness (buồn), normal (bình thường), angry (tức giận). "
    "Chỉ trả lời đúng một từ là tên nhãn, không giải thích,độ tín cậy cao."
)


def doc_nhan(text):
    """Tìm nhãn trong câu trả lời của Gemini. Có nhiều nhãn thì lấy nhãn xuất hiện đầu tiên.
    Không thấy nhãn nào thì trả về None."""
    t = (text or "").lower()
    tim = [(t.find(n), n) for n in NHAN if n in t]
    return min(tim)[1] if tim else None


def nhan_dien_cam_xuc():
    """Camera chạy + có người -> lấy 5 ảnh -> Gemini phân loại -> xoá ảnh.

    Trả về "excited" / "sadness" / "normal" / "angry".
    Trả về None nếu không phân loại được: camera lỗi, không có người, không lấy được ảnh,
    gọi Gemini thất bại, hoặc Gemini trả lời không phải 1 trong 4 nhãn. Không ném exception.
    Ảnh chỉ nằm trong bộ nhớ (không lưu ra file) và luôn bị xoá ở cuối, kể cả khi lỗi.
    """
    if anh.xac_nhan_co_nguoi() != 1:
        log.info("camera lỗi hoặc không có người -> không gửi ảnh")
        return None

    anh_list = anh.anh_duyet()       # 5 ảnh / 5 giây
    parts = []                       # ảnh đã nén JPEG để gửi đi
    try:
        if not anh_list:
            log.error("không lấy được ảnh từ camera")
            return None

        for a in anh_list:
            ok, jpeg = cv2.imencode(".jpg", a)
            if ok:
                parts.append(types.Part.from_bytes(data=jpeg.tobytes(), mime_type="image/jpeg"))
        if not parts:
            log.error("không nén được ảnh sang JPEG")
            return None

        client = genai.Client(http_options=types.HttpOptions(timeout=TIMEOUT_S * 1000))   # tự đọc GEMINI_API_KEY
        resp = client.models.generate_content(
            model=MODEL,
            contents=parts + [CAU_HOI],
            config=types.GenerateContentConfig(temperature=0),    # phân loại nên cho trả lời ổn định
        )
        nhan = doc_nhan(resp.text)
        if nhan is None:
            log.warning("Gemini trả lời không thuộc 4 nhãn: %r", resp.text)
        else:
            log.info("cảm xúc: %s", nhan)
        return nhan
    except Exception:
        log.exception("lỗi khi gửi ảnh lên Gemini")
        return None 
    finally:
        anh_list.clear()             # xoá ảnh gốc khỏi bộ nhớ
        parts.clear()                # xoá luôn bản JPEG đã nén
        log.info("đã xoá ảnh khỏi bộ nhớ")



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    ket_qua = nhan_dien_cam_xuc()
    print(f"\n--- CẢM XÚC: {ket_qua} ---")
