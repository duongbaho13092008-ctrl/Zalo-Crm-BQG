"""Tiện ích xử lý chữ tiếng Việt: bỏ dấu, tách câu, tách từ khoá."""

from __future__ import annotations

import re
import unicodedata

_KHOANG_TRANG = re.compile(r"\s+")
_KY_TU_LA = re.compile(r"[^a-z0-9]+")
# Ngắt câu sau . ! ? … và xuống dòng; không ngắt giữa số thập phân "1.5"
_NGAT_CAU = re.compile(r"(?<=[.!?…])(?<!\d\.)\s+|\n+")
_EMOJI = re.compile(
    "[\U0001f000-\U0001faff\U00002600-\U000027bf\U0001f900-\U0001f9ff‍️]+",
    flags=re.UNICODE,
)

# Từ dừng — không dùng để khớp cảnh
TU_DUNG = {
    "va", "la", "cua", "cho", "voi", "nhung", "thi", "ma", "co", "khong", "duoc", "mot",
    "cac", "nhieu", "nay", "do", "kia", "roi", "se", "da", "dang", "bang", "neu", "khi",
    "de", "o", "tai", "tu", "ra", "vao", "len", "xuong", "con", "ba", "anh", "chi", "em",
    "minh", "ban", "chung", "toi", "ta", "nha", "a", "nhe", "ha", "oi", "ay", "thoi",
}


def bo_dau(chu: str) -> str:
    """'Máy ép cám' -> 'May ep cam' (đổi cả đ/Đ)."""
    chu = chu.replace("đ", "d").replace("Đ", "D")
    tach = unicodedata.normalize("NFD", chu)
    return "".join(c for c in tach if unicodedata.category(c) != "Mn")


def slug(chu: str) -> str:
    """'Viên cám ra khuôn' -> 'vien-cam-ra-khuon'."""
    return _KY_TU_LA.sub("-", bo_dau(chu).lower()).strip("-")


def tu_khoa(chu: str) -> list[str]:
    """Tách từ khoá không dấu, bỏ từ dừng: 'Máy chạy êm' -> ['may', 'chay', 'em']."""
    return [t for t in slug(chu).split("-") if t and t not in TU_DUNG]


def bo_emoji(chu: str) -> str:
    return _EMOJI.sub("", chu)


def gon(chu: str) -> str:
    return _KHOANG_TRANG.sub(" ", chu).strip()


def tach_cau(doan: str) -> list[str]:
    """Tách đoạn văn thành câu, bỏ câu rỗng."""
    doan = bo_emoji(doan)
    return [gon(c) for c in _NGAT_CAU.split(doan) if gon(c)]


def chia_cau_dai(cau: str, toi_da_ky_tu: int) -> list[str]:
    """Chia câu dài thành các mẩu ≤ toi_da_ky_tu, ưu tiên ngắt ở dấu phẩy rồi khoảng trắng."""
    cau = gon(cau)
    if len(cau) <= toi_da_ky_tu:
        return [cau]
    manh: list[str] = []
    for phan in re.split(r"(?<=[,;:])\s+", cau):
        if len(phan) <= toi_da_ky_tu:
            manh.append(phan)
            continue
        tu = phan.split(" ")
        dong = ""
        for t in tu:
            thu = f"{dong} {t}".strip()
            if len(thu) > toi_da_ky_tu and dong:
                manh.append(dong)
                dong = t
            else:
                dong = thu
        if dong:
            manh.append(dong)
    # gộp mẩu quá ngắn vào mẩu trước
    ket_qua: list[str] = []
    for m in manh:
        if ket_qua and len(m) < 8 and len(ket_qua[-1]) + 1 + len(m) <= toi_da_ky_tu + 8:
            ket_qua[-1] = f"{ket_qua[-1]} {m}"
        else:
            ket_qua.append(m)
    return ket_qua


def dem_tu(chu: str) -> int:
    return len([t for t in gon(chu).split(" ") if t])
