import logging
import signal
import socket
import sys
import threading

import psutil

from online import Online

log = logging.getLogger("robot.main")

RAM_LIMIT = 90          # %
RAM_LIEN_TIEP = 5       # phải vượt ngưỡng 5 lần liên tiếp (~5s) mới coi là nguy hiểm, bỏ qua đỉnh thoáng qua
NHIP_RAM = 1.0
LOI_DE_OFFLINE = 2      # mất mạng 2 lần kiểm tra liền (~6s) mới chuyển offline -> mạng chập chờn không làm bật/tắt liên tục
NHIP_MANG = 3.0
# Kiểm tra bằng TCP tới IP công cộng (không cần DNS, không phụ thuộc NetworkManager)
DIEM_KIEM_TRA = (("1.1.1.1", 443), ("8.8.8.8", 53))


def co_mang():
    """[M2] Thay cho `nmcli ... CONNECTIVITY` (giá trị đó chỉ được làm mới ~5 phút/lần)."""
    for host, port in DIEM_KIEM_TRA:
        try:
            with socket.create_connection((host, port), timeout=2):
                return True
        except OSError:
            continue
    return False


def giam_sat_ram(thoat, ma_thoat):
    """[M1] Vượt ngưỡng liên tục mới thoát GỌN với mã lỗi khác 0 để systemd (Restart=on-failure) bật lại."""
    vuot = 0
    while not thoat.wait(NHIP_RAM):
        if psutil.virtual_memory().percent >= RAM_LIMIT:
            vuot += 1
            if vuot >= RAM_LIEN_TIEP:
                log.critical("RAM >= %d%% liên tục %d lần -> thoát để khởi động lại", RAM_LIMIT, vuot)
                ma_thoat[0] = 1
                thoat.set()
                return
        else:
            vuot = 0


def che_do_offline():
    """Khi rớt mạng / không có mạng: không gọi Gemini, hiện mặt Normal.
    TODO: thêm hành vi offline (nhạc/lời thoại có sẵn trong máy) tại đây."""
    log.info("chế độ OFFLINE")


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    thoat = threading.Event()
    ma_thoat = [0]

    # systemd stop = SIGTERM -> thoát gọn
    signal.signal(signal.SIGTERM, lambda *_: thoat.set())
    signal.signal(signal.SIGINT, lambda *_: thoat.set())

    threading.Thread(target=giam_sat_ram, args=(thoat, ma_thoat), name="ram", daemon=True).start()

    online = Online()
    che_do = None           # None / "online" / "offline"
    loi = 0

    try:
        while not thoat.is_set():
            mang = co_mang()
            loi = 0 if mang else loi + 1

            if che_do is None:                              # lần đầu: quyết định ngay
                muon = "online" if mang else "offline"
            elif mang:
                muon = "online"
            elif loi >= LOI_DE_OFFLINE:
                muon = "offline"
            else:
                muon = che_do                               # chập chờn: giữ nguyên

            if muon != che_do:
                log.info("chuyển chế độ: %s -> %s", che_do, muon)
                if muon == "online":
                    online.start()
                else:
                    online.stop()                           # dừng nhạc/luồng online trước
                    che_do_offline()
                che_do = muon

            thoat.wait(NHIP_MANG)
    finally:
        online.stop()
        log.info("đã dừng")
    return ma_thoat[0]


if __name__ == "__main__":
    sys.exit(main())