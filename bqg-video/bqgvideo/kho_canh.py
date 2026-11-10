"""Khâu 5 — Kho cảnh thật của BQG và khớp cảnh theo thứ tự kịch bản.

Quy ước đặt tệp (xem kho-canh/README.md):
    kho-canh/<dong-may>/<the-1>_<the-2>_<the-3>_<so>.mp4
Ví dụ:
    kho-canh/may-ep-cam-vien/may-chay_vien-cam_khuon-6ly_01.mp4
    kho-canh/chung/nha-xuong_tho-han_03.jpg

Mỗi cụm nối gạch ngang là một THẺ; thư mục là DÒNG MÁY. Không dùng kho ảnh miễn phí trên mạng:
video BQG phải là máy BQG chạy thật.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from pathlib import Path

from .brand import DONG_MAY, THU_MUC_CHUNG
from .media import do_thoi_luong
from .van_ban import slug, tu_khoa

DUOI_VIDEO = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi"}
DUOI_ANH = {".jpg", ".jpeg", ".png", ".webp"}


@dataclass
class Canh:
    duong_dan: Path
    dong_may: str
    the: list[str]
    la_anh: bool
    thoi_luong: float | None = None
    tu: set[str] = field(default_factory=set)

    @property
    def ten(self) -> str:
        return f"{self.dong_may}/{self.duong_dan.name}"


def the_tu_ten_tep(ten: str) -> list[str]:
    goc = Path(ten).stem
    the = []
    for phan in goc.split("_"):
        s = slug(phan)
        if s and not s.isdigit():
            the.append(s)
    return the




class KhoCanh:
    def __init__(self, thu_muc: Path, can_thoi_luong: bool = True):
        self.thu_muc = Path(thu_muc)
        self.canh: list[Canh] = []
        self._quet(can_thoi_luong)

    def _quet(self, can_thoi_luong: bool) -> None:
        if not self.thu_muc.exists():
            return
        for tep in sorted(self.thu_muc.rglob("*")):
            duoi = tep.suffix.lower()
            if not tep.is_file() or duoi not in DUOI_VIDEO | DUOI_ANH:
                continue
            tuong_doi = tep.relative_to(self.thu_muc)
            dong_may = tuong_doi.parts[0] if len(tuong_doi.parts) > 1 else THU_MUC_CHUNG
            the = the_tu_ten_tep(tep.name)
            la_anh = duoi in DUOI_ANH
            c = Canh(
                duong_dan=tep,
                dong_may=dong_may,
                the=the,
                la_anh=la_anh,
                thoi_luong=None if la_anh or not can_thoi_luong else do_thoi_luong(tep),
            )
            c.tu = {t for th in the for t in th.split("-")}
            self.canh.append(c)

    # ---- thống kê ----
    def tat_ca_the(self) -> list[str]:
        return sorted({t for c in self.canh for t in c.the})

    def thong_ke(self) -> dict[str, dict]:
        kq: dict[str, dict] = {}
        for slug_may in list(DONG_MAY) + sorted({c.dong_may for c in self.canh} - set(DONG_MAY)):
            ds = [c for c in self.canh if c.dong_may == slug_may]
            kq[slug_may] = {
                "so_video": sum(not c.la_anh for c in ds),
                "so_anh": sum(c.la_anh for c in ds),
                "tong_giay": round(sum(c.thoi_luong or 0 for c in ds), 1),
                "the": sorted({t for c in ds for t in c.the}),
            }
        return kq

    # ---- khớp cảnh ----
    @staticmethod
    def _diem(canh: Canh, the_muon: list[str], tu_loi: list[str], dong_may: str) -> float:
        the_muon_s = {slug(t) for t in the_muon if slug(t)}
        diem = 3.0 * len(the_muon_s & set(canh.the))
        tu_muon = {w for t in the_muon_s for w in t.split("-")} | set(tu_loi)
        diem += 1.0 * len(tu_muon & canh.tu)
        if canh.dong_may == dong_may:
            diem += 2.0
        elif canh.dong_may != THU_MUC_CHUNG:
            diem -= 100  # không bao giờ lấy cảnh máy KHÁC dòng
        if not canh.la_anh:
            diem += 0.5  # ưu tiên video hơn ảnh tĩnh
        return diem

    def chon_canh(
        self,
        cac_doan: list[tuple[list[str], str]],
        dong_may: str,
        seed: int | None = None,
    ) -> list[Canh | None]:
        """Chọn 1 cảnh cho mỗi đoạn (thẻ muốn, lời đọc). Tránh lặp cảnh khi còn cảnh chưa dùng.

        Trả None cho đoạn không có cảnh phù hợp (sẽ dựng nền thương hiệu).
        """
        ngau_nhien = random.Random(seed)
        hop_le = [c for c in self.canh if c.dong_may in (dong_may, THU_MUC_CHUNG)]
        da_dung: dict[Path, int] = {}
        ket_qua: list[Canh | None] = []
        for the_muon, loi in cac_doan:
            if not hop_le:
                ket_qua.append(None)
                continue
            tu_loi = tu_khoa(loi)
            cham = []
            for c in hop_le:
                d = self._diem(c, the_muon, tu_loi, dong_may) - 4.0 * da_dung.get(c.duong_dan, 0)
                cham.append((d, ngau_nhien.random(), c))
            cham.sort(key=lambda x: (x[0], x[1]), reverse=True)
            tot_nhat = cham[0][2]
            da_dung[tot_nhat.duong_dan] = da_dung.get(tot_nhat.duong_dan, 0) + 1
            ket_qua.append(tot_nhat)
        return ket_qua
