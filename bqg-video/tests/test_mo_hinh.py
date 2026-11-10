import pytest

from bqgvideo.mo_hinh import KichBan, YeuCauDung, YeuCauKichBan, tach_dong_the

VB = """MO: Bà con nuôi cá mà tiền cám ăn hết lãi?
MO: Một giờ ra 300 kg cám nổi.
Đây là máy ép cám viên đang chạy. [may-chay, vien-cam]
Viên ra đều, nổi lâu.
Bà con nhắn Zalo cho Bình Quân."""


def test_tu_van_ban():
    kb = KichBan.tu_van_ban(VB, chu_de="Cám nổi")
    assert len(kb.cau_mo_dau) == 2
    assert kb.than_bai[0].the_canh == ["may-chay", "vien-cam"]
    assert kb.keu_goi == "Bà con nhắn Zalo cho Bình Quân."
    # mọi biến thể chung thân bài + kêu gọi, chỉ khác câu mở đầu
    a, b = kb.loi_doc(0).splitlines(), kb.loi_doc(1).splitlines()
    assert a[0] != b[0] and a[1:] == b[1:]
    assert len(kb.cac_doan(1)) == 4


def test_tu_van_ban_khong_co_mo():
    kb = KichBan.tu_van_ban("Câu một.\nCâu hai.\nCâu ba.")
    assert kb.cau_mo_dau == ["Câu một."] and kb.keu_goi == "Câu ba."


def test_tach_dong_the():
    d = tach_dong_the("Viên ra đều [vien-cam,  khuon ]")
    assert d.loi == "Viên ra đều" and d.the_canh == ["vien-cam", "khuon"]


def test_kiem_hop_le():
    with pytest.raises(ValueError):
        YeuCauKichBan(chu_de="x", dong_may="may-bay")
    with pytest.raises(ValueError):
        YeuCauDung(kich_ban=KichBan(), giong="giong-la")
    with pytest.raises(ValueError):
        YeuCauDung(kich_ban=KichBan(), ti_le="4:3")
