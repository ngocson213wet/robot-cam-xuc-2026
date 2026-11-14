import os
import time
import pygame

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

THOI_GIAN_PHAT = 75     # giây phát đủ âm lượng
THOI_GIAN_GIAM = 15     # giây giảm dần rồi tắt
AM_LUONG_MP3 = 0.5      # nhạc nền 30%
AM_LUONG_WAV = 1        # wav 100%


def chay_nhac(file_wav, file_mp3):
    pygame.mixer.init()

    wav_path = os.path.join(BASE_DIR, file_wav)
    mp3_path = os.path.join(BASE_DIR, file_mp3)

    am_wav = pygame.mixer.Sound(wav_path)
    am_wav.set_volume(AM_LUONG_WAV)

    pygame.mixer.music.load(mp3_path)
    pygame.mixer.music.set_volume(AM_LUONG_MP3)

    pygame.mixer.music.play(loops=-1)       # lặp lại nếu bài ngắn hơn 45 giây
    am_wav.play()
    bat_dau = time.time()

    while True:
        da_troi = time.time() - bat_dau

        if da_troi < THOI_GIAN_PHAT:
            pass                            # đang phát bình thường

        elif da_troi < THOI_GIAN_PHAT + THOI_GIAN_GIAM:
            # Đang giảm dần: từ 30% xuống 0%
            tien_do = (da_troi - THOI_GIAN_PHAT) / THOI_GIAN_GIAM
            pygame.mixer.music.set_volume(AM_LUONG_MP3 * (1 - tien_do))

        else:
            pygame.mixer.music.stop()       # hết 15 giây giảm thì tắt
            break

        pygame.time.wait(100)

    # Đợi file wav phát nốt nếu chưa xong
    while pygame.mixer.get_busy():
        pygame.time.wait(100)

    print("đã chạy xong")


if __name__ == "__main__":
    chay_nhac("thoai_excited/excited.wav", "thoai_excited/nhacnen2.mp3")