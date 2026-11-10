import pytest

from bqgvideo.an_danh import an_danh


@pytest.mark.parametrize("sdt", ["0912345678", "0912 345 678", "0912.345.678", "+84 912 345 678", "84912345678"])
def test_an_so_dien_thoai(sdt):
    kq = an_danh(f"Khách gọi {sdt} hỏi máy")
    assert sdt not in kq.van_ban
    assert kq.co_du_lieu_nhay_cam


def test_an_email_lien_ket_so_tai_khoan():
    kq = an_danh("Mail a.b@gmail.com, zalo.me/0912345678, STK 1903 4567 8901 234")
    assert "gmail" not in kq.van_ban and "zalo.me" not in kq.van_ban and "1903" not in kq.van_ban


def test_khong_an_so_lieu_san_xuat():
    kq = an_danh("Máy chạy 300 kg/giờ, khuôn 6 ly, nuôi 2000 con gà từ năm 1990")
    assert kq.van_ban == "Máy chạy 300 kg/giờ, khuôn 6 ly, nuôi 2000 con gà từ năm 1990"
    assert not kq.co_du_lieu_nhay_cam
