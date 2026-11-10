"""Dây chuyền 6 khâu: Kịch bản -> Thẻ cảnh -> Giọng đọc -> Phụ đề -> Cảnh thật -> Dựng & chờ duyệt.

Không có khâu tự đăng: video dựng xong ở trạng thái CHỜ DUYỆT.
"""

from __future__ import annotations

import math
import re
import zlib
from pathlib import Path
from typing import Callable

from loguru import logger

from .ai_viet import viet_kich_ban
from .brand import ten_dong_may
from .cau_hinh import CauHinh
from .dung_video import Shot, dung
from .giong_doc import can_doan, doc_bang_edge, dung_tep_ghi_am, khong_giong
from .kho_canh import KhoCanh
from .kiem_duyet import kiem_tra
from .mo_hinh import BanGhiVideo, KichBan, YeuCauDung, YeuCauKichBan
from .phu_de import ghi_srt, tao_phu_de
from .so_do import SoDo, bay_gio, tao_ma

BaoTienDo = Callable[[str, float], None]


def _khong_bao(_: str, __: float) -> None:
    pass


def so_cho_phep(ch: CauHinh) -> tuple[str, ...]:
    """Số của chính BQG (hotline, Zalo) không bị coi là 'số liệu chưa có bằng chứng'."""
    ket_qua: list[str] = []
    for gia_tri in (ch.thuong_hieu.hotline, ch.thuong_hieu.zalo):
        ket_qua += re.findall(r"\d+", gia_tri)  # từng cụm số
        if len(re.sub(r"\D", "", gia_tri)) >= 9:
            ket_qua.append(re.sub(r"\D", "", gia_tri))  # cả số điện thoại
    return tuple(ket_qua)


def kiem_kich_ban(ch: CauHinh, kb: KichBan) -> list[list[dict]]:
    """Kiểm từng biến thể; trả danh sách cảnh báo theo biến thể."""
    so_bt = max(1, len(kb.cau_mo_dau))
    return [
        [c.to_dict() for c in kiem_tra(kb.loi_doc(i), kb.bang_chung, so_cho_phep(ch))] for i in range(so_bt)
    ]


def tao_kich_ban(ch: CauHinh, yc: YeuCauKichBan) -> dict:
    kho = KhoCanh(ch.thu_muc_kho_canh, can_thoi_luong=False)
    the = sorted({t for c in kho.canh if c.dong_may in (yc.dong_may, "chung") for t in c.the})
    kb, da_an = viet_kich_ban(ch, yc, the)
    return {"kich_ban": kb, "da_an_truoc_khi_gui_ai": da_an, "canh_bao": kiem_kich_ban(ch, kb)}


def _tep_nhac(ch: CauHinh, ten: str | None) -> Path | None:
    if not ten:
        return None
    if Path(ten).name != ten:
        raise ValueError("Tên tệp nhạc không hợp lệ.")
    tep = ch.thu_muc_nhac / ten
    if not tep.exists():
        raise ValueError(f"Không thấy tệp nhạc: {ten}")
    return tep


def chia_shot(doan_moc: list[tuple[float, float, list]], giay_toi_da: float) -> list[tuple[int, float, float]]:
    """Đoạn dài hơn giay_toi_da được chia thành nhiều cú máy để nhịp video không lê thê."""
    shots = []
    for k, (bd, kt, _) in enumerate(doan_moc):
        n = max(1, math.ceil((kt - bd) / giay_toi_da - 1e-9))
        buoc = (kt - bd) / n
        for j in range(n):
            shots.append((k, bd + j * buoc, bd + (j + 1) * buoc))
    return shots


def dung_mot_bien_the(
    ch: CauHinh,
    yc: YeuCauDung,
    bien_the: int,
    so_do: SoDo,
    kho: KhoCanh,
    bao: BaoTienDo = _khong_bao,
) -> BanGhiVideo:
    kb = yc.kich_ban
    ma = tao_ma(kb.dong_may, yc.so_chu_de, bien_the)
    if so_do.ton_tai(ma) and so_do.doc(ma).trang_thai not in ("loi",):
        raise ValueError(f"Mã {ma} đã có video — chọn số chủ đề khác.")
    thu_muc = so_do.thu_muc(ma)
    thu_muc.mkdir(parents=True, exist_ok=True)

    cac_doan = kb.cac_doan(bien_the)
    loi_doc = kb.loi_doc(bien_the)
    bg = BanGhiVideo(
        ma=ma,
        chu_de=kb.chu_de,
        dong_may=kb.dong_may,
        bien_the=bien_the,
        cau_mo_dau=kb.cau_mo_dau[bien_the] if kb.cau_mo_dau else "",
        loi_doc=loi_doc,
        tao_luc=bay_gio(),
        giong=yc.giong,
        ti_le=yc.ti_le,
        canh_bao=[c.to_dict() for c in kiem_tra(loi_doc, kb.bang_chung, so_cho_phep(ch))],
    )
    so_do.luu(bg)
    (thu_muc / "loi-doc.txt").write_text(loi_doc, encoding="utf-8")
    (thu_muc / "kich-ban.json").write_text(kb.model_dump_json(indent=2), encoding="utf-8")

    try:
        bao(f"{ma}: tạo giọng đọc", 0.1)
        texts = [d.loi for d in cac_doan]
        if yc.giong == "tep-ghi-am":
            if not yc.tep_ghi_am:
                raise ValueError("Chọn giọng 'tệp ghi âm' thì phải tải tệp ghi âm lên.")
            giong = dung_tep_ghi_am(Path(yc.tep_ghi_am), texts, thu_muc / "giong")
        elif yc.giong == "khong-giong":
            giong = khong_giong(texts)
        else:
            giong = doc_bang_edge(texts, yc.giong, yc.toc_do, thu_muc / "giong.mp3")

        bao(f"{ma}: khớp cảnh thật", 0.3)
        doan_moc = can_doan(texts, giong.tu_moc, giong.thoi_luong)
        shot_raw = chia_shot(doan_moc, ch.video.giay_toi_da_moi_canh)
        chon = kho.chon_canh(
            [(cac_doan[k].the_canh, cac_doan[k].loi) for k, _, _ in shot_raw],
            kb.dong_may,
            seed=zlib.crc32(ma.encode()),
        )
        shots = [Shot(bd, kt, c) for (_, bd, kt), c in zip(shot_raw, chon)]
        bg.canh_da_dung = [c.ten if c else "(nền thương hiệu — thiếu cảnh thật)" for c in chon]
        bg.thieu_canh_that = any(c is None for c in chon)

        phu_de = None
        if yc.phu_de:
            phu_de = tao_phu_de(doan_moc, ch.video.so_ky_tu_toi_da_moi_dong)
            ghi_srt(phu_de, thu_muc / "phu-de.srt")
            bg.tep_phu_de = "phu-de.srt"

        bao(f"{ma}: dựng video", 0.5)
        tong = dung(
            ch,
            shots,
            phu_de,
            giong.tep_am_thanh,
            giong.thoi_luong,
            ma,
            yc.ti_le,
            thu_muc / "video.mp4",
            tep_nhac=_tep_nhac(ch, yc.nhac_nen),
            ten_dong_may=ten_dong_may(kb.dong_may),
            seed=zlib.crc32(ma.encode()),
        )
        bg.tep_video = "video.mp4"
        bg.thoi_luong_giay = round(tong, 2)
        bg.trang_thai = "cho_duyet"
        bg.loi = None
        bao(f"{ma}: xong — chờ duyệt", 1.0)
    except Exception as e:  # ghi lỗi vào bản ghi để người dùng thấy
        logger.exception(f"Dựng {ma} lỗi")
        bg.trang_thai = "loi"
        bg.loi = f"{type(e).__name__}: {e}"
    return so_do.luu(bg)


def dung_bo_video(ch: CauHinh, yc: YeuCauDung, bao: BaoTienDo = _khong_bao) -> list[BanGhiVideo]:
    """Dựng các biến thể câu mở đầu của một chủ đề (mặc định: tất cả)."""
    so_bt = max(1, len(yc.kich_ban.cau_mo_dau))
    ds_bt = yc.cac_bien_the if yc.cac_bien_the is not None else list(range(so_bt))
    if any(b < 0 or b >= so_bt for b in ds_bt):
        raise ValueError(f"Biến thể phải trong khoảng 0..{so_bt - 1}")
    if yc.giong == "tep-ghi-am" and len(ds_bt) > 1:
        raise ValueError("Một tệp ghi âm chỉ khớp một biến thể câu mở đầu — chọn đúng 1 biến thể.")
    if not yc.kich_ban.than_bai and not yc.kich_ban.cau_mo_dau:
        raise ValueError("Kịch bản trống.")
    so_do = SoDo(ch.thu_muc_du_lieu)
    kho = KhoCanh(ch.thu_muc_kho_canh)
    if not kho.canh:
        logger.warning("Kho cảnh trống — video sẽ dùng nền thương hiệu và bị đánh dấu thiếu cảnh thật.")
    return [dung_mot_bien_the(ch, yc, b, so_do, kho, bao) for b in ds_bt]
