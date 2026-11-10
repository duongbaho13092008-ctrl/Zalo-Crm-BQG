"""Hằng số thương hiệu và nghiệp vụ của Bình Quân Group."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

TEN_CONG_TY = "Bình Quân Group"
TEN_PHAP_LY = "Công ty TNHH Thương mại và Sản xuất Bình Quân"
KHAU_HIEU = "Đồng hành cùng nhà nông từ 1990"

# Màu nhận diện (lấy từ logo: xanh lá đậm, vàng bông lúa, xanh dương)
MAU_CHINH = "#14532D"
MAU_PHU = "#1E6FD9"
MAU_NHAN = "#F5C518"
MAU_CHU_SANG = "#FFFFFF"

THU_MUC_GOC = Path(__file__).resolve().parent.parent
THU_MUC_TAI_NGUYEN = THU_MUC_GOC / "resource"
FONT_DAM = THU_MUC_TAI_NGUYEN / "fonts" / "BeVietnamPro-Bold.ttf"
FONT_VUA = THU_MUC_TAI_NGUYEN / "fonts" / "BeVietnamPro-Medium.ttf"
LOGO = THU_MUC_TAI_NGUYEN / "logo-bqg.png"


@dataclass(frozen=True)
class DongMay:
    slug: str  # tên thư mục trong kho cảnh
    ma: str  # mã ngắn dùng trong mã video
    ten: str  # tên hiển thị
    the_goi_y: tuple[str, ...] = field(default_factory=tuple)


DONG_MAY: dict[str, DongMay] = {
    d.slug: d
    for d in (
        DongMay(
            "may-ep-cam-vien",
            "EPCAM",
            "Máy ép cám viên",
            ("may-chay", "vien-cam", "khuon", "cam-noi", "nuoi-ca", "nuoi-lon", "nuoi-ga", "nang-suat"),
        ),
        DongMay("may-nghien", "NGHIEN", "Máy nghiền", ("may-chay", "nghien-ngo", "bot-min", "luoi")),
        DongMay("may-tron", "TRON", "Máy trộn", ("may-chay", "tron-cam", "dau-tron")),
        DongMay("may-bam-co", "BAMCO", "Máy băm cỏ, băm chuối", ("may-chay", "bam-co", "bam-chuoi", "nuoi-bo")),
        DongMay("may-ep-dau", "EPDAU", "Máy ép dầu", ("may-chay", "dau-lac", "dau-vung", "ocop")),
        DongMay("may-bam-xo-dua", "XODUA", "Máy băm xơ dừa", ("may-chay", "xo-dua")),
        DongMay("phu-tung", "PHUTUNG", "Phụ tùng, khuôn, dao, lưới", ("khuon", "dao", "luoi", "thay-the")),
        DongMay(
            "chung",
            "CHUNG",
            "Cảnh chung (nhà xưởng, giao lắp, khách hàng)",
            ("nha-xuong", "giao-lap", "khach-hang", "nghiem-thu", "tho-han"),
        ),
    )
}

DONG_MAY_MAC_DINH = "may-ep-cam-vien"
THU_MUC_CHUNG = "chung"

# Bộ lọc 4 câu — lead đủ 4 câu mới là SQL (lead đủ tiêu chuẩn Sales)
BON_CAU_LOC = (
    "Nuôi / chế biến gì, quy mô bao nhiêu",
    "Đang tự trộn hay mua cám ngoài",
    "Ai là người quyết mua",
    "Định làm trong bao lâu",
)

# Ba kiểu câu mở đầu để thử — mỗi biến thể chỉ đổi MỘT yếu tố: câu mở đầu
KIEU_CAU_MO_DAU = (
    "Câu hỏi đúng nỗi đau của bà con",
    "Con số bằng chứng thật",
    "Cảnh máy chạy / kết quả nhìn thấy ngay",
)

GIONG_DOC = {
    "vi-VN-HoaiMyNeural": "Hoài My — nữ, giọng Bắc (máy, miễn phí)",
    "vi-VN-NamMinhNeural": "Nam Minh — nam, giọng Bắc (máy, miễn phí)",
    "tep-ghi-am": "Tệp ghi âm người thật (tải lên)",
    "khong-giong": "Không lồng tiếng (chỉ phụ đề)",
}
GIONG_MAC_DINH = "vi-VN-HoaiMyNeural"

TI_LE_KHUNG = {
    "9:16": (1080, 1920),
    "16:9": (1920, 1080),
    "1:1": (1080, 1080),
}

# Danh mục kiểm khi duyệt — tất cả phải tích thì mới được duyệt
CHECKLIST_DUYET = {
    "so_lieu_dung": "Số năng suất / số liệu đúng với bằng chứng đã xác minh",
    "khong_hua_qua": "Không hứa quá: không cam kết lãi, không hứa ngày giao, không 'tốt nhất / số 1'",
    "dung_may": "Cảnh, tên máy, cấu hình khớp đúng dòng máy được nói",
    "khong_lo_khach": "Không lộ tên, số điện thoại, mặt khách khi chưa được đồng ý",
    "nhac_hop_le": "Nhạc nền có quyền sử dụng (hoặc không dùng nhạc)",
    "ma_video_hien": "Mã video hiện rõ ở cảnh kết để đo lead",
}

TRANG_THAI = {
    "dang_dung": "Đang dựng",
    "loi": "Lỗi khi dựng",
    "cho_duyet": "Chờ duyệt",
    "da_duyet": "Đã duyệt",
    "tu_choi": "Từ chối — cần sửa",
    "da_dang": "Đã đăng",
}

KENH_DANG = ("TikTok", "Facebook Reels", "YouTube Shorts", "Zalo", "Website", "Khác")


def ten_dong_may(slug: str) -> str:
    d = DONG_MAY.get(slug)
    return d.ten if d else slug
