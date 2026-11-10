"""Ẩn danh dữ liệu khách trước khi gửi cho A.I hoặc đưa vào kịch bản.

Lọc được: số điện thoại Việt Nam, email, chuỗi số dài (CCCD, số tài khoản), link Zalo/Facebook cá nhân.
KHÔNG lọc được tên người — người duyệt vẫn phải đọc lại (checklist 'khong_lo_khach').
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_MAU = [
    (
        "so_dien_thoai",
        re.compile(r"(?<!\d)(?:\+?84|0)(?:[\s.\-]?\d){8,10}(?!\d)"),
        "[SĐT đã ẩn]",
    ),
    ("email", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[email đã ẩn]"),
    (
        "lien_ket_ca_nhan",
        re.compile(r"(?:https?://)?(?:www\.)?(?:zalo\.me|facebook\.com|fb\.com|m\.me)/[^\s,]+", re.I),
        "[liên kết đã ẩn]",
    ),
    ("chuoi_so_dai", re.compile(r"(?<!\d)\d(?:[\s.\-]?\d){8,18}(?!\d)"), "[số đã ẩn]"),
]


@dataclass
class KetQuaAnDanh:
    van_ban: str
    da_an: dict[str, int]

    @property
    def co_du_lieu_nhay_cam(self) -> bool:
        return any(self.da_an.values())


def an_danh(van_ban: str) -> KetQuaAnDanh:
    da_an: dict[str, int] = {}
    for ten, mau, thay in _MAU:
        van_ban, so = mau.subn(thay, van_ban)
        if so:
            da_an[ten] = da_an.get(ten, 0) + so
    return KetQuaAnDanh(van_ban, da_an)


def tim_du_lieu_nhay_cam(van_ban: str) -> dict[str, int]:
    return an_danh(van_ban).da_an
