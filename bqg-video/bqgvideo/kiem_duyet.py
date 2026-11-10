"""Kiểm kịch bản trước khi dựng: chặn lời hứa quá, số liệu không có bằng chứng, dữ liệu khách.

Hai mức:
- "chan": phải sửa kịch bản, video có lỗi này KHÔNG được duyệt.
- "canh_bao": người duyệt phải đọc kỹ và tự quyết.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass

from .an_danh import tim_du_lieu_nhay_cam
from .van_ban import bo_dau

CHAN = "chan"
CANH_BAO = "canh_bao"

# Cụm từ cường điệu / hứa quá — so khớp trên chữ không dấu, chữ thường
TU_CAM: dict[str, str] = {
    "tot nhat": "So sánh tuyệt đối 'tốt nhất' — không chứng minh được",
    "so 1": "Tự xưng 'số 1' — không chứng minh được",
    "so mot": "Tự xưng 'số một' — không chứng minh được",
    "re nhat": "'Rẻ nhất' — không chứng minh được, dễ bị so giá",
    "duy nhat": "'Duy nhất' — không chứng minh được",
    "cam ket 100": "Cam kết tuyệt đối",
    "bao dam lai": "Hứa lãi",
    "dam bao lai": "Hứa lãi",
    "chac chan lai": "Hứa lãi",
    "lai khung": "Hứa lãi, cường điệu",
    "sieu loi nhuan": "Hứa lãi, cường điệu",
    "hoan von ngay": "Hứa hoàn vốn",
    "bao lo": "Hứa bao lỗ",
    "khong bao gio hong": "Hứa không hỏng",
    "vinh vien": "Hứa vĩnh viễn",
    "than ky": "Cường điệu",
    "than thanh": "Cường điệu",
    "giau nhanh": "Hứa làm giàu",
}

# Cụm cần người duyệt xem lại (không chặn)
TU_CAN_XEM: dict[str, str] = {
    "gia chi": "Có nhắc giá — đối chiếu bảng giá hiện hành, chính sách báo giá",
    "gia re": "Có nhắc giá — đối chiếu bảng giá hiện hành",
    "trieu dong": "Có nhắc số tiền — đối chiếu bảng giá / bằng chứng",
    "vnd": "Có nhắc số tiền — đối chiếu bảng giá / bằng chứng",
    "giao ngay": "Hứa thời gian giao — chỉ nói khi xưởng xác nhận",
    "giao trong": "Hứa thời gian giao — chỉ nói khi xưởng xác nhận",
    "mien phi": "Có chữ 'miễn phí' — kiểm điều kiện khuyến mãi đang chạy",
    "khuyen mai": "Khuyến mãi — kiểm còn hiệu lực",
    "bao hanh tron doi": "Hứa bảo hành trọn đời — kiểm chính sách bảo hành",
    "hoan von": "Nói về hoàn vốn — phải có bài toán hoàn vốn và giả định rõ",
}

# Số đi kèm đơn vị — loại số cần bằng chứng
_SO_LIEU = re.compile(
    r"(?<![\w])(\d+(?:[.,]\d+)?)\s*"
    r"(%|phan tram|kg|ky|ki lo|tan|ta|yen|gio|tieng|phut|ngay|thang|nam|trieu|nghin|ngan|k|dong|kw|hp|ngua|"
    r"con|ha|sao|mau|lit|vong|ly|mm|cm|m)(?![a-z])",
)
_SO_DUNG_SAN = {"1990"}  # năm thành lập trong khẩu hiệu


@dataclass
class CanhBao:
    muc: str
    noi_dung: str
    trich: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _chuan_so(s: str) -> str:
    return s.replace(",", ".")


def _cac_so_trong(van_ban_khong_dau: str) -> set[str]:
    return {_chuan_so(m) for m in re.findall(r"\d+(?:[.,]\d+)?", van_ban_khong_dau)}


def kiem_tra(
    kich_ban: str,
    bang_chung: str = "",
    so_cho_phep: tuple[str, ...] = (),
) -> list[CanhBao]:
    """Trả về danh sách cảnh báo cho một kịch bản (chuỗi lời đọc)."""
    ket_qua: list[CanhBao] = []
    kich_ban = unicodedata.normalize("NFC", kich_ban)
    thuong = bo_dau(kich_ban).lower()  # cùng độ dài với kich_ban => cắt trích đúng chữ có dấu
    goc = kich_ban if len(kich_ban) == len(thuong) else thuong

    for bang, muc in ((TU_CAM, CHAN), (TU_CAN_XEM, CANH_BAO)):
        for cum, ly_do in bang.items():
            m = re.search(rf"(?<![a-z0-9]){re.escape(bo_dau(cum).lower())}(?![a-z0-9])", thuong)
            if m:
                ket_qua.append(CanhBao(muc, ly_do, goc[m.start() : m.end()]))

    # số điện thoại của chính BQG (hotline, Zalo OA) được phép đọc trong video
    van_ban_loc = kich_ban
    for so in so_cho_phep:
        chu_so = re.sub(r"\D", "", so)
        if len(chu_so) >= 9:
            if chu_so.startswith("0"):
                chu_so = chu_so[1:]
            mau = r"(?:\+?84|0)[\s.\-]?" + r"[\s.\-]?".join(chu_so)
            van_ban_loc = re.sub(mau, " ", van_ban_loc)
    nhay_cam = tim_du_lieu_nhay_cam(van_ban_loc)
    for loai, so in nhay_cam.items():
        ket_qua.append(CanhBao(CHAN, f"Kịch bản chứa dữ liệu cá nhân ({loai} × {so}) — xoá trước khi dựng"))

    so_bang_chung = _cac_so_trong(bo_dau(bang_chung).lower()) | _SO_DUNG_SAN | {
        _chuan_so(s) for s in so_cho_phep
    }
    da_bao: set[str] = set()
    for m in _SO_LIEU.finditer(thuong):
        so = _chuan_so(m.group(1))
        if so in so_bang_chung or so in da_bao:
            continue
        da_bao.add(so)
        ket_qua.append(
            CanhBao(
                CANH_BAO,
                "Số liệu chưa có trong phần bằng chứng đã xác minh — người duyệt kiểm lại",
                goc[m.start() : m.end()],
            )
        )
    return ket_qua


def co_loi_chan(ds: list[CanhBao] | list[dict]) -> bool:
    for c in ds:
        muc = c["muc"] if isinstance(c, dict) else c.muc
        if muc == CHAN:
            return True
    return False
