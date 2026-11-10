from bqgvideo.giong_doc import TuMoc, can_doan, khong_giong, uoc_moc
from bqgvideo.phu_de import ghi_srt, tao_phu_de

DOAN = ["Bà con nuôi cá mà tiền cám ăn hết lãi?", "Đây là máy ép cám viên đang chạy.", "Nhắn Zalo cho Bình Quân."]


def test_uoc_moc_phu_kin_thoi_luong():
    moc = uoc_moc(DOAN, 12.0)
    assert moc[0].bat_dau == 0 and abs(moc[-1].ket_thuc - 12.0) < 1e-6
    assert len(moc) == sum(len(d.split()) for d in DOAN)


def test_can_doan_lien_mach():
    moc = uoc_moc(DOAN, 12.0)
    doan = can_doan(DOAN, moc, 12.5)
    assert len(doan) == 3
    assert doan[0][0] == 0 and doan[-1][1] == 12.5
    for a, b in zip(doan, doan[1:]):
        assert a[1] == b[0]
    assert [t.chu for t in doan[1][2]] == DOAN[1].split()


def test_can_doan_voi_moc_that_co_so():
    # máy đọc trả "300" là một từ, kịch bản cũng "300"
    doan_text = ["Một giờ ra 300 kg.", "Bà con xem nhé."]
    tu = "Một giờ ra 300 kg. Bà con xem nhé.".split()
    moc = [TuMoc(t, i * 0.5, i * 0.5 + 0.4) for i, t in enumerate(tu)]
    doan = can_doan(doan_text, moc, 5.0)
    assert [t.chu for t in doan[0][2]] == ["Một", "giờ", "ra", "300", "kg."]


def test_khong_giong():
    kq = khong_giong(DOAN)
    assert kq.tep_am_thanh is None and kq.thoi_luong >= 5


def test_phu_de_gioi_han_do_dai(tmp_path):
    moc = uoc_moc(DOAN, 12.0)
    pd = tao_phu_de(can_doan(DOAN, moc, 12.0), toi_da_ky_tu=15)
    assert all(len(d.chu) <= 30 or " " not in d.chu for d in pd)
    assert all(d.ket_thuc > d.bat_dau for d in pd)
    tep = ghi_srt(pd, tmp_path / "a.srt")
    noi_dung = tep.read_text(encoding="utf-8")
    assert noi_dung.startswith("1\n00:00:00,000 --> ")
