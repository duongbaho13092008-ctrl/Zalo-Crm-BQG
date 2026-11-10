"""Mã nguồn video + sổ theo dõi: duyệt, đăng, và số đo lead đủ 4 câu lọc / đơn máy thực.

Mỗi video có một MÃ duy nhất, hiện trên video và ở cảnh kết: V-<DÒNG MÁY>-<YYMMDD>-<CHỦ ĐỀ><BIẾN THỂ>
Ví dụ V-EPCAM-261110-01B = máy ép cám, ngày 10/11/2026, chủ đề số 1, biến thể câu mở đầu B.
Sales ghi mã này vào trường "nguồn" của khách trên CRM => đếm được lead và đơn theo từng video.

Luật số đo: ô trống = "Chưa có dữ liệu", KHÔNG phải số 0. Không tự suy số.
"""

from __future__ import annotations

import csv
import io
import json
import re
import threading
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode, urlparse, urlunparse, parse_qsl

from .brand import CHECKLIST_DUYET, DONG_MAY, ten_dong_may
from .kiem_duyet import co_loi_chan
from .mo_hinh import BanGhiVideo, DoLuong, Duyet, LanDang

CHUA_CO = "Chưa có dữ liệu"
_MAU_MA = re.compile(r"^V-[A-Z]+-\d{6}-\d{2}[A-Z]$")
_khoa = threading.Lock()


def bay_gio() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def tao_ma(dong_may: str, so_chu_de: int, bien_the: int, ngay: datetime | None = None) -> str:
    ma_may = DONG_MAY[dong_may].ma if dong_may in DONG_MAY else "KHAC"
    ngay = ngay or datetime.now()
    return f"V-{ma_may}-{ngay:%y%m%d}-{so_chu_de:02d}{chr(ord('A') + bien_the)}"


def ma_hop_le(ma: str) -> bool:
    return bool(_MAU_MA.match(ma))


def gan_utm(lien_ket: str, ma: str, kenh: str) -> str:
    """Gắn mã video vào link website/landing để đo nguồn (utm_content = mã video)."""
    p = urlparse(lien_ket)
    q = dict(parse_qsl(p.query))
    q.update(
        {
            "utm_source": re.sub(r"[^a-z0-9]+", "-", kenh.lower()).strip("-") or "video",
            "utm_medium": "video-ngan",
            "utm_campaign": ma.rsplit("-", 1)[0],
            "utm_content": ma,
        }
    )
    return urlunparse(p._replace(query=urlencode(q)))


class SoDo:
    """Lưu bản ghi mỗi video ở <data>/videos/<mã>/ban-ghi.json."""

    def __init__(self, thu_muc_du_lieu: Path):
        self.goc = Path(thu_muc_du_lieu) / "videos"
        self.goc.mkdir(parents=True, exist_ok=True)

    def thu_muc(self, ma: str) -> Path:
        if not ma_hop_le(ma):
            raise ValueError(f"Mã video không hợp lệ: {ma}")
        return self.goc / ma

    def _tep(self, ma: str) -> Path:
        return self.thu_muc(ma) / "ban-ghi.json"

    def ton_tai(self, ma: str) -> bool:
        return self._tep(ma).exists()

    def luu(self, bg: BanGhiVideo) -> BanGhiVideo:
        tep = self._tep(bg.ma)
        tep.parent.mkdir(parents=True, exist_ok=True)
        tam = tep.with_suffix(".tmp")
        with _khoa:
            tam.write_text(bg.model_dump_json(indent=2), encoding="utf-8")
            tam.replace(tep)
        return bg

    def doc(self, ma: str) -> BanGhiVideo:
        tep = self._tep(ma)
        if not tep.exists():
            raise KeyError(f"Không có video mã {ma}")
        return BanGhiVideo.model_validate_json(tep.read_text(encoding="utf-8"))

    def danh_sach(self, trang_thai: str | None = None) -> list[BanGhiVideo]:
        ds = []
        for tep in sorted(self.goc.glob("*/ban-ghi.json")):
            try:
                bg = BanGhiVideo.model_validate_json(tep.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                continue
            if trang_thai is None or bg.trang_thai == trang_thai:
                ds.append(bg)
        ds.sort(key=lambda b: b.tao_luc, reverse=True)
        return ds

    # ---- duyệt ----
    def duyet(self, ma: str, nguoi_duyet: str, checklist: dict[str, bool], dong_y: bool, ghi_chu: str = "") -> BanGhiVideo:
        bg = self.doc(ma)
        if bg.trang_thai not in ("cho_duyet", "tu_choi", "da_duyet"):
            raise ValueError(f"Video đang ở trạng thái '{bg.trang_thai}', không duyệt được.")
        if not nguoi_duyet.strip():
            raise ValueError("Phải ghi tên người duyệt.")
        if dong_y:
            thieu = [CHECKLIST_DUYET[k] for k in CHECKLIST_DUYET if not checklist.get(k)]
            if thieu:
                raise ValueError("Chưa tích đủ danh mục kiểm: " + "; ".join(thieu))
            if co_loi_chan(bg.canh_bao):
                raise ValueError("Kịch bản còn lỗi CHẶN (hứa quá / dữ liệu khách) — sửa kịch bản và dựng lại.")
        elif not ghi_chu.strip():
            raise ValueError("Từ chối thì phải ghi lý do để người dựng sửa.")
        bg.lich_su_duyet.append(
            Duyet(nguoi_duyet=nguoi_duyet.strip(), dong_y=dong_y, checklist=checklist, ghi_chu=ghi_chu, luc=bay_gio())
        )
        bg.trang_thai = "da_duyet" if dong_y else "tu_choi"
        return self.luu(bg)

    def ghi_dang(self, ma: str, kenh: str, lien_ket: str = "", nguoi_dang: str = "") -> BanGhiVideo:
        bg = self.doc(ma)
        if bg.trang_thai not in ("da_duyet", "da_dang"):
            raise ValueError("Chỉ video ĐÃ DUYỆT mới được ghi nhận đăng.")
        bg.lan_dang.append(LanDang(kenh=kenh, lien_ket=lien_ket, luc=bay_gio(), nguoi_dang=nguoi_dang))
        bg.trang_thai = "da_dang"
        return self.luu(bg)

    def cap_nhat_do_luong(self, ma: str, **so: int | str | None) -> BanGhiVideo:
        bg = self.doc(ma)
        du_lieu = bg.do_luong.model_dump()
        for k, v in so.items():
            if k not in du_lieu or k == "cap_nhat_luc":
                raise ValueError(f"Trường số đo không hợp lệ: {k}")
            if v is not None and k != "nguon_so" and int(v) < 0:
                raise ValueError(f"{k} không được âm")
            du_lieu[k] = v
        moi = DoLuong(**du_lieu)
        if moi.lead_du_4_cau is not None and moi.lead is not None and moi.lead_du_4_cau > moi.lead:
            raise ValueError("Số lead đủ 4 câu lọc không thể lớn hơn tổng lead — kiểm lại số.")
        if moi.don_may_thuc is not None and moi.lead_du_4_cau is not None and moi.don_may_thuc > moi.lead_du_4_cau:
            raise ValueError("Số đơn máy thực lớn hơn số lead đủ 4 câu lọc — kiểm lại cách gắn mã.")
        moi.cap_nhat_luc = bay_gio()
        bg.do_luong = moi
        return self.luu(bg)

    # ---- tổng hợp ----
    def tong_hop_chu_de(self) -> list[dict]:
        """So các biến thể câu mở đầu trong cùng chủ đề (cùng tiền tố mã)."""
        nhom: dict[str, list[BanGhiVideo]] = {}
        for bg in self.danh_sach():
            nhom.setdefault(bg.ma[:-1], []).append(bg)
        ket_qua = []
        for tien_to, ds in sorted(nhom.items(), reverse=True):
            ds.sort(key=lambda b: b.bien_the)
            ket_qua.append(
                {
                    "chu_de": ds[0].chu_de,
                    "dong_may": ten_dong_may(ds[0].dong_may),
                    "tien_to": tien_to,
                    "bien_the": [
                        {
                            "ma": b.ma,
                            "cau_mo_dau": b.cau_mo_dau,
                            "trang_thai": b.trang_thai,
                            "lead_du_4_cau": b.do_luong.lead_du_4_cau,
                            "don_may_thuc": b.do_luong.don_may_thuc,
                        }
                        for b in ds
                    ],
                    "du_du_lieu": all(b.do_luong.lead_du_4_cau is not None for b in ds),
                }
            )
        return ket_qua

    def xuat_csv(self) -> str:
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(
            [
                "ma_video", "ngay_tao", "dong_may", "chu_de", "bien_the", "cau_mo_dau", "trang_thai",
                "nguoi_duyet", "kenh_dang", "lien_ket", "luot_xem", "lead", "lead_du_4_cau", "don_may_thuc",
                "nguon_so", "cap_nhat_so_luc",
            ]
        )
        for b in self.danh_sach():
            duyet = next((d for d in reversed(b.lich_su_duyet) if d.dong_y), None)
            dl = b.do_luong

            def o(v):
                return CHUA_CO if v is None else v

            w.writerow(
                [
                    b.ma, b.tao_luc[:10], ten_dong_may(b.dong_may), b.chu_de, chr(ord("A") + b.bien_the),
                    b.cau_mo_dau, b.trang_thai, duyet.nguoi_duyet if duyet else "",
                    "; ".join(d.kenh for d in b.lan_dang), "; ".join(d.lien_ket for d in b.lan_dang if d.lien_ket),
                    o(dl.luot_xem), o(dl.lead), o(dl.lead_du_4_cau), o(dl.don_may_thuc),
                    dl.nguon_so or "", dl.cap_nhat_luc or "",
                ]
            )
        return buf.getvalue()

    def tim_so_chu_de_tiep(self, dong_may: str, ngay: datetime | None = None) -> int:
        tien_to = tao_ma(dong_may, 1, 0, ngay)[:-3]
        da_co = [int(p.name[len(tien_to) : len(tien_to) + 2]) for p in self.goc.glob(f"{tien_to}*") if p.is_dir()]
        return (max(da_co) + 1) if da_co else 1


def doc_json(tep: Path) -> dict:
    return json.loads(Path(tep).read_text(encoding="utf-8"))
