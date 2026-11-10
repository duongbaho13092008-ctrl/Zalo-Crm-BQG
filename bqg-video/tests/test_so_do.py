from datetime import datetime

import pytest

from bqgvideo.brand import CHECKLIST_DUYET
from bqgvideo.mo_hinh import BanGhiVideo
from bqgvideo.so_do import CHUA_CO, SoDo, gan_utm, ma_hop_le, tao_ma

DU = {k: True for k in CHECKLIST_DUYET}


def test_tao_ma():
    ma = tao_ma("may-ep-cam-vien", 3, 1, datetime(2026, 11, 10))
    assert ma == "V-EPCAM-261110-03B" and ma_hop_le(ma)
    assert not ma_hop_le("../../etc")


def bg(ma="V-EPCAM-261110-01A", **kw):
    kw.setdefault("trang_thai", "cho_duyet")
    return BanGhiVideo(ma=ma, chu_de="Cám nổi", dong_may="may-ep-cam-vien", bien_the=ord(ma[-1]) - 65,
                       cau_mo_dau="Mở", loi_doc="Mở", tao_luc="2026-11-10T09:00:00", **kw)


def test_duyet_can_du_checklist_va_ten(tmp_path):
    sd = SoDo(tmp_path)
    sd.luu(bg())
    with pytest.raises(ValueError, match="danh mục"):
        sd.duyet("V-EPCAM-261110-01A", "Lan", {**DU, "dung_may": False}, True)
    with pytest.raises(ValueError, match="tên"):
        sd.duyet("V-EPCAM-261110-01A", " ", DU, True)
    with pytest.raises(ValueError, match="lý do"):
        sd.duyet("V-EPCAM-261110-01A", "Lan", {}, False)
    assert sd.duyet("V-EPCAM-261110-01A", "Lan", DU, True).trang_thai == "da_duyet"


def test_loi_chan_khong_duyet_duoc(tmp_path):
    sd = SoDo(tmp_path)
    sd.luu(bg(canh_bao=[{"muc": "chan", "noi_dung": "Hứa lãi", "trich": ""}]))
    with pytest.raises(ValueError, match="CHẶN"):
        sd.duyet("V-EPCAM-261110-01A", "Lan", DU, True)


def test_chua_duyet_khong_dang(tmp_path):
    sd = SoDo(tmp_path)
    sd.luu(bg())
    with pytest.raises(ValueError, match="ĐÃ DUYỆT"):
        sd.ghi_dang("V-EPCAM-261110-01A", "TikTok")
    sd.duyet("V-EPCAM-261110-01A", "Lan", DU, True)
    assert sd.ghi_dang("V-EPCAM-261110-01A", "TikTok", "https://t/1").trang_thai == "da_dang"


def test_do_luong_va_csv(tmp_path):
    sd = SoDo(tmp_path)
    sd.luu(bg())
    sd.luu(bg("V-EPCAM-261110-01B"))
    sd.luu(bg("V-EPCAM-261110-02A", trang_thai="loi"))  # bản dựng hỏng không vào sổ đo
    with pytest.raises(ValueError):
        sd.cap_nhat_do_luong("V-EPCAM-261110-01A", lead=3, lead_du_4_cau=5)
    with pytest.raises(ValueError):
        sd.cap_nhat_do_luong("V-EPCAM-261110-01A", lead_du_4_cau=1, don_may_thuc=2)
    with pytest.raises(ValueError):
        sd.cap_nhat_do_luong("V-EPCAM-261110-01A", lead=-1)
    sd.cap_nhat_do_luong("V-EPCAM-261110-01A", lead=10, lead_du_4_cau=4, don_may_thuc=1, nguon_so="CRM")
    csv = sd.xuat_csv()
    assert CHUA_CO in csv  # biến thể B chưa có số
    assert "02A" not in csv
    th = sd.tong_hop_chu_de()
    assert len(th) == 1 and len(th[0]["bien_the"]) == 2 and th[0]["du_du_lieu"] is False
    assert th[0]["bien_the"][0]["lead_du_4_cau"] == 4 and th[0]["bien_the"][1]["lead_du_4_cau"] is None


def test_so_chu_de_tiep(tmp_path):
    sd = SoDo(tmp_path)
    ngay = datetime.now()
    assert sd.tim_so_chu_de_tiep("may-ep-cam-vien", ngay) == 1
    sd.luu(bg(tao_ma("may-ep-cam-vien", 4, 0, ngay)))
    assert sd.tim_so_chu_de_tiep("may-ep-cam-vien", ngay) == 5


def test_utm():
    lk = gan_utm("https://binhquan.vn/may-ep-cam?x=1", "V-EPCAM-261110-01A", "TikTok")
    assert "x=1" in lk and "utm_content=V-EPCAM-261110-01A" in lk and "utm_source=tiktok" in lk
