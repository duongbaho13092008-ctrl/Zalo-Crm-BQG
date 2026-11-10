"""Khâu 3 — Giọng đọc, và khâu 4 — mốc thời gian để làm phụ đề, chuyển cảnh.

- Giọng máy: Edge TTS, 2 giọng tiếng Việt miễn phí (Hoài My nữ, Nam Minh nam), có mốc từng từ.
- Tệp ghi âm người thật (giọng miền, giọng kỹ thuật viên BQG): mốc chia theo độ dài chữ.
- Không giọng: thời lượng ước theo tốc độ đọc 2,6 từ/giây.
"""

from __future__ import annotations

import asyncio
import shutil
from dataclasses import dataclass
from pathlib import Path

from loguru import logger

from .media import do_thoi_luong
from .van_ban import gon, slug

TU_MOI_GIAY = 2.6
_TICK = 10_000_000  # Edge TTS tính thời gian theo đơn vị 100 nano giây


@dataclass
class TuMoc:
    chu: str
    bat_dau: float
    ket_thuc: float


@dataclass
class KetQuaGiong:
    tep_am_thanh: Path | None
    thoi_luong: float
    tu_moc: list[TuMoc]
    moc_that: bool  # True = mốc thật từ máy đọc; False = mốc ước lượng


class LoiGiong(RuntimeError):
    pass


def _toc_do_edge(toc_do: float) -> str:
    return f"{round((toc_do - 1.0) * 100):+d}%"


async def _edge_async(van_ban: str, giong: str, toc_do: float, tep_ra: Path) -> list[TuMoc]:
    import edge_tts

    giao_tiep = edge_tts.Communicate(van_ban, giong, rate=_toc_do_edge(toc_do), boundary="WordBoundary")
    moc: list[TuMoc] = []
    with open(tep_ra, "wb") as f:
        async for manh in giao_tiep.stream():
            if manh["type"] == "audio":
                f.write(manh["data"])
            elif manh["type"] == "WordBoundary":
                bd = manh["offset"] / _TICK
                moc.append(TuMoc(manh["text"], bd, bd + manh["duration"] / _TICK))
    return moc


def thoi_luong_am_thanh(tep: Path) -> float:
    tl = do_thoi_luong(tep)
    if not tl:
        raise LoiGiong(f"Không đọc được thời lượng tệp âm thanh: {Path(tep).name}")
    return tl


def doc_bang_edge(cac_doan: list[str], giong: str, toc_do: float, tep_ra: Path) -> KetQuaGiong:
    # Mỗi đoạn kết thúc bằng dấu câu để máy đọc ngắt nghỉ tự nhiên
    van_ban = " ".join(d if d.rstrip()[-1:] in ".!?…" else f"{d}." for d in cac_doan)
    try:
        moc = asyncio.run(_edge_async(van_ban, giong, toc_do, tep_ra))
    except Exception as e:  # mạng chặn, dịch vụ đổi API...
        raise LoiGiong(
            f"Không tạo được giọng đọc Edge TTS ({type(e).__name__}: {e}). "
            "Kiểm tra mạng tới speech.platform.bing.com, hoặc dùng tệp ghi âm."
        ) from e
    if not tep_ra.exists() or tep_ra.stat().st_size == 0:
        raise LoiGiong("Edge TTS không trả âm thanh.")
    tl = thoi_luong_am_thanh(tep_ra)
    if not moc:
        logger.warning("Edge TTS không trả mốc từ — dùng mốc ước lượng.")
        return KetQuaGiong(tep_ra, tl, uoc_moc(cac_doan, tl), False)
    return KetQuaGiong(tep_ra, tl, moc, True)


def dung_tep_ghi_am(tep_nguon: Path, cac_doan: list[str], tep_ra: Path) -> KetQuaGiong:
    if not Path(tep_nguon).exists():
        raise LoiGiong(f"Không thấy tệp ghi âm: {tep_nguon}")
    tep_ra = tep_ra.with_suffix(Path(tep_nguon).suffix.lower() or ".mp3")
    shutil.copyfile(tep_nguon, tep_ra)
    tl = thoi_luong_am_thanh(tep_ra)
    return KetQuaGiong(tep_ra, tl, uoc_moc(cac_doan, tl), False)


def khong_giong(cac_doan: list[str]) -> KetQuaGiong:
    so_tu = sum(len(gon(d).split()) for d in cac_doan)
    tl = max(5.0, so_tu / TU_MOI_GIAY)
    return KetQuaGiong(None, tl, uoc_moc(cac_doan, tl), False)


def uoc_moc(cac_doan: list[str], tong_giay: float) -> list[TuMoc]:
    """Chia đều thời lượng cho từng từ theo độ dài chữ (dùng khi không có mốc thật)."""
    tu = [t for d in cac_doan for t in gon(d).split(" ") if t]
    if not tu:
        return []
    trong_so = [len(t) + 1 for t in tu]
    tong = sum(trong_so)
    moc, t = [], 0.0
    for chu, w in zip(tu, trong_so):
        dai = tong_giay * w / tong
        moc.append(TuMoc(chu, t, t + dai))
        t += dai
    return moc


def _so_token(chu: str) -> int:
    return len([x for x in slug(chu).split("-") if x])


def can_doan(cac_doan: list[str], tu_moc: list[TuMoc], tong_giay: float) -> list[tuple[float, float, list[TuMoc]]]:
    """Gắn từng đoạn kịch bản với mốc thời gian của nó.

    Trả về [(bắt đầu, kết thúc, các từ của đoạn)], liền mạch từ 0 tới tong_giay.
    """
    ket_qua: list[tuple[float, float, list[TuMoc]]] = []
    i = 0
    for so_doan, doan in enumerate(cac_doan):
        can = _so_token(doan)
        tu_cua_doan: list[TuMoc] = []
        dem = 0
        while i < len(tu_moc) and (dem < can or not tu_cua_doan):
            tu_cua_doan.append(tu_moc[i])
            dem += max(1, _so_token(tu_moc[i].chu))
            i += 1
        if so_doan == len(cac_doan) - 1 and i < len(tu_moc):
            tu_cua_doan.extend(tu_moc[i:])  # đoạn cuối nhận phần còn dư
            i = len(tu_moc)
        if tu_cua_doan:
            ket_qua.append((tu_cua_doan[0].bat_dau, tu_cua_doan[-1].ket_thuc, tu_cua_doan))
        else:
            ket_qua.append((ket_qua[-1][1] if ket_qua else 0.0, tong_giay, []))

    # làm liền mạch: đoạn đầu từ 0, mỗi đoạn kéo tới đầu đoạn sau, đoạn cuối tới hết âm thanh
    lien: list[tuple[float, float, list[TuMoc]]] = []
    for k, (bd, kt, tu) in enumerate(ket_qua):
        bd = 0.0 if k == 0 else lien[-1][1]
        kt = ket_qua[k + 1][0] if k + 1 < len(ket_qua) else tong_giay
        lien.append((bd, max(kt, bd + 0.3), tu))
    return lien
