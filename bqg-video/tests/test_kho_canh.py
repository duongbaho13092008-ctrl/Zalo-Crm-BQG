from pathlib import Path

from bqgvideo.kho_canh import KhoCanh, the_tu_ten_tep


def tao(goc: Path, *ten: str) -> None:
    for t in ten:
        p = goc / t
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"")


def test_the_tu_ten_tep():
    assert the_tu_ten_tep("May chay_Viên cám_khuon-6ly_01.mp4") == ["may-chay", "vien-cam", "khuon-6ly"]


def test_khong_lay_canh_may_khac_dong(tmp_path):
    tao(tmp_path, "may-ep-cam-vien/may-chay_vien-cam_01.mp4", "may-ep-dau/may-chay_dau-lac_01.mp4",
        "chung/nha-xuong_01.jpg")
    kho = KhoCanh(tmp_path, can_thoi_luong=False)
    chon = kho.chon_canh([(["dau-lac"], "ép dầu lạc")] * 4, "may-ep-cam-vien", seed=1)
    assert all(c is not None and c.dong_may in ("may-ep-cam-vien", "chung") for c in chon)


def test_uu_tien_the_khop_va_tranh_lap(tmp_path):
    tao(tmp_path, "may-ep-cam-vien/may-chay_01.mp4", "may-ep-cam-vien/vien-cam_khuon_02.mp4",
        "may-ep-cam-vien/khach-hang_cam-vien_03.mp4")
    kho = KhoCanh(tmp_path, can_thoi_luong=False)
    c1, c2 = kho.chon_canh([(["khuon"], "khuôn mới"), (["khuon"], "khuôn mới")], "may-ep-cam-vien", seed=1)
    assert c1.duong_dan.name == "vien-cam_khuon_02.mp4"
    assert c2.duong_dan != c1.duong_dan  # còn cảnh khác thì không lặp


def test_kho_trong_tra_none(tmp_path):
    kho = KhoCanh(tmp_path / "khong-co", can_thoi_luong=False)
    assert kho.chon_canh([(["may-chay"], "x")], "may-ep-cam-vien") == [None]


def test_thong_ke(tmp_path):
    tao(tmp_path, "may-ep-cam-vien/may-chay_01.mp4", "may-ep-cam-vien/vien-cam_02.jpg")
    tk = KhoCanh(tmp_path, can_thoi_luong=False).thong_ke()
    assert tk["may-ep-cam-vien"]["so_video"] == 1 and tk["may-ep-cam-vien"]["so_anh"] == 1
    assert tk["may-nghien"]["so_video"] == 0
