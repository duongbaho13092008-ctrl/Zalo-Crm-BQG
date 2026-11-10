from bqgvideo.van_ban import bo_dau, chia_cau_dai, slug, tach_cau, tu_khoa


def test_bo_dau_va_slug():
    assert bo_dau("Máy ép cám Đồng Tháp") == "May ep cam Dong Thap"
    assert slug("Viên cám ra khuôn 6 ly!") == "vien-cam-ra-khuon-6-ly"


def test_tu_khoa_bo_tu_dung():
    assert tu_khoa("Máy chạy rất bền và khoẻ, anh chị nhé") == ["may", "chay", "rat", "ben", "khoe"]


def test_tach_cau_khong_cat_so_thap_phan():
    cau = tach_cau("Máy chạy 1.5 tấn mỗi giờ. Bà con xem nhé!\nNhắn Zalo 🙂")
    assert cau == ["Máy chạy 1.5 tấn mỗi giờ.", "Bà con xem nhé!", "Nhắn Zalo"]


def test_chia_cau_dai():
    manh = chia_cau_dai("Đây là máy ép cám viên đang chạy ở trại cá, viên ra đều và nổi lâu trên mặt nước", 30)
    assert all(len(m) <= 38 for m in manh)
    assert " ".join(manh).replace("  ", " ").startswith("Đây là máy ép cám viên")
