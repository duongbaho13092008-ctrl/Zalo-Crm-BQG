from bqgvideo.kiem_duyet import CANH_BAO, CHAN, co_loi_chan, kiem_tra


def muc(ds):
    return [c.muc for c in ds]


def test_chan_cuong_dieu():
    for cau in ["Máy tốt nhất miền Bắc", "Số 1 Việt Nam", "Đảm bảo lãi ngay", "Hoàn vốn ngay sau 1 vụ"]:
        assert CHAN in muc(kiem_tra(cau)), cau


def test_khong_bat_nham_tu_ghep():
    assert kiem_tra("Bà con xem máy chạy thật") == []


def test_so_lieu_can_bang_chung():
    ds = kiem_tra("Máy chạy 300 kg mỗi giờ")
    assert muc(ds) == [CANH_BAO]
    assert kiem_tra("Máy chạy 300 kg mỗi giờ", bang_chung="Đo tại trại: 300 kg/giờ") == []
    assert kiem_tra("Máy chạy 1,5 tấn mỗi giờ", bang_chung="1.5 tấn/giờ") == []


def test_nam_thanh_lap_va_so_cua_bqg_duoc_phep():
    assert kiem_tra("Đồng hành cùng nhà nông từ 1990") == []
    # hotline của BQG được đọc trong video; số điện thoại khác vẫn bị chặn
    assert kiem_tra("Gọi 0912 345 678 nhé", so_cho_phep=("0912345678",)) == []
    assert kiem_tra("Gọi +84 912.345.678 nhé", so_cho_phep=("0912345678",)) == []
    assert co_loi_chan(kiem_tra("Anh Tư 0987 654 321 mua rồi", so_cho_phep=("0912345678",)))


def test_nhac_gia_thi_canh_bao():
    ds = kiem_tra("Giá chỉ hơn chục triệu đồng")
    assert CANH_BAO in muc(ds) and not co_loi_chan(ds)


def test_co_loi_chan_nhan_dict():
    assert co_loi_chan([{"muc": "chan"}]) and not co_loi_chan([{"muc": "canh_bao"}])
