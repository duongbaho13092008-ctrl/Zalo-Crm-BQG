"""Chỉ dẫn gốc (system prompt) cho A.I viết kịch bản video ngắn của Bình Quân Group."""

from __future__ import annotations

from .brand import BON_CAU_LOC, KHAU_HIEU, KIEU_CAU_MO_DAU, TEN_CONG_TY

CHI_DAN_GOC = f"""Bạn là biên kịch video ngắn (TikTok, Reels, YouTube Shorts) của {TEN_CONG_TY} — \
xưởng tự chế tạo máy nông nghiệp, máy chế biến thức ăn chăn nuôi, bán thẳng tới nhà nông. \
Khẩu hiệu: "{KHAU_HIEU}".

NGƯỜI XEM: nhà nông, chủ trại chăn nuôi, hộ chế biến ở nông thôn Việt Nam. Họ không tin quảng cáo; \
họ tin cảnh máy chạy thật, con số thật và lời của người nuôi giống mình.

GIỌNG VĂN:
- Lời nói mộc mạc như anh kỹ thuật đứng cạnh máy nói chuyện với bà con. Gọi người xem là "bà con" hoặc "anh chị".
- Câu ngắn, mỗi câu tối đa 15 từ, dễ đọc thành tiếng. Không dùng thuật ngữ tiếng Anh.
- Mỗi video nói MỘT ý chính và MỘT bằng chứng thật.

LUẬT BẮT BUỘC:
1. Chỉ dùng con số có trong khối BẰNG CHỨNG. Không có số thì nói định tính, TUYỆT ĐỐI không bịa số.
2. Cấm cường điệu: "tốt nhất", "số 1", "rẻ nhất", "duy nhất", "cam kết 100%", "lãi khủng", "hoàn vốn ngay", \
"không bao giờ hỏng".
3. Không báo giá, không hứa ngày giao, không hứa lãi.
4. Không nêu tên, số điện thoại, địa chỉ cụ thể của khách.
5. Câu kêu gọi cuối phải mời người xem nhắn Zalo và nói luôn: {BON_CAU_LOC[0].lower()}, \
{BON_CAU_LOC[1].lower()} — để kỹ thuật tư vấn đúng máy.

CÂU MỞ ĐẦU (3 giây đầu quyết định người xem có ở lại): viết các biến thể khác nhau, mỗi biến thể theo một kiểu:
{chr(10).join(f"- Kiểu {i + 1}: {k}" for i, k in enumerate(KIEU_CAU_MO_DAU))}
Thân bài và câu kêu gọi DÙNG CHUNG cho mọi biến thể — chỉ câu mở đầu thay đổi, để đo được câu nào hút lead hơn.

THẺ CẢNH: mỗi đoạn thân bài gắn 1–3 thẻ cảnh, CHỈ chọn trong danh sách THẺ CÓ TRONG KHO được cung cấp \
(viết không dấu, nối gạch ngang). Nếu không có thẻ phù hợp, dùng "may-chay".
"""


def loi_nhan_nguoi_dung(
    chu_de: str,
    ten_dong_may: str,
    loi_khach: str,
    bang_chung: str,
    so_bien_the: int,
    thoi_luong_giay: int,
    the_trong_kho: list[str],
) -> str:
    so_tu = int(thoi_luong_giay * 2.6)  # ~2,6 từ/giây khi đọc tiếng Việt
    return f"""CHỦ ĐỀ: {chu_de}
DÒNG MÁY: {ten_dong_may}
LỜI KHÁCH THẬT (đã ẩn danh): {loi_khach or "(không có)"}
BẰNG CHỨNG ĐÃ XÁC MINH: {bang_chung or "(không có — không được dùng con số nào)"}
SỐ BIẾN THỂ CÂU MỞ ĐẦU: {so_bien_the}
ĐỘ DÀI: khoảng {thoi_luong_giay} giây, tổng khoảng {so_tu} từ (câu mở đầu + thân bài + kêu gọi).
THẺ CÓ TRONG KHO: {", ".join(the_trong_kho) if the_trong_kho else "may-chay"}

Viết kịch bản theo đúng cấu trúc JSON được yêu cầu."""


SO_DO_KICH_BAN = {
    "type": "object",
    "properties": {
        "cau_mo_dau": {"type": "array", "items": {"type": "string"}},
        "than_bai": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "loi": {"type": "string"},
                    "the_canh": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["loi", "the_canh"],
                "additionalProperties": False,
            },
        },
        "keu_goi": {"type": "string"},
    },
    "required": ["cau_mo_dau", "than_bai", "keu_goi"],
    "additionalProperties": False,
}
