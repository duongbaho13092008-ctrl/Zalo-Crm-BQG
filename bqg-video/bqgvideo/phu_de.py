"""Khâu 4 — Phụ đề: chia dòng theo độ rộng chữ thật, xuất tệp .srt, vẽ ảnh phụ đề."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .giong_doc import TuMoc


@dataclass
class DongPhuDe:
    bat_dau: float
    ket_thuc: float
    chu: str


def tao_phu_de(
    cac_doan_co_moc: list[tuple[float, float, list[TuMoc]]],
    toi_da_ky_tu: int = 22,
    toi_da_dong: int = 2,
) -> list[DongPhuDe]:
    """Gom từ thành từng câu phụ đề ≤ (toi_da_ky_tu × toi_da_dong) ký tự, không vắt qua 2 đoạn."""
    gioi_han = toi_da_ky_tu * toi_da_dong
    ket_qua: list[DongPhuDe] = []
    for bd_doan, kt_doan, tu in cac_doan_co_moc:
        nhom: list[TuMoc] = []
        for t in tu:
            thu = " ".join(x.chu for x in nhom + [t])
            if nhom and len(thu) > gioi_han:
                ket_qua.append(DongPhuDe(nhom[0].bat_dau, nhom[-1].ket_thuc, " ".join(x.chu for x in nhom)))
                nhom = []
            nhom.append(t)
            # ngắt sau dấu câu nếu đã đủ dài
            if t.chu[-1:] in ".!?,;:" and len(" ".join(x.chu for x in nhom)) >= toi_da_ky_tu:
                ket_qua.append(DongPhuDe(nhom[0].bat_dau, nhom[-1].ket_thuc, " ".join(x.chu for x in nhom)))
                nhom = []
        if nhom:
            ket_qua.append(DongPhuDe(nhom[0].bat_dau, nhom[-1].ket_thuc, " ".join(x.chu for x in nhom)))
    # kéo mỗi dòng tới đầu dòng sau (tránh nháy trống), tối thiểu 0,6 giây
    for k in range(len(ket_qua) - 1):
        ket_qua[k].ket_thuc = max(ket_qua[k].ket_thuc, min(ket_qua[k + 1].bat_dau, ket_qua[k].bat_dau + 6))
    for d in ket_qua:
        d.ket_thuc = max(d.ket_thuc, d.bat_dau + 0.6)
    return ket_qua


def _moc_srt(giay: float) -> str:
    ms = int(round(giay * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def ghi_srt(dong: list[DongPhuDe], tep: Path) -> Path:
    phan = [f"{i}\n{_moc_srt(d.bat_dau)} --> {_moc_srt(d.ket_thuc)}\n{d.chu}\n" for i, d in enumerate(dong, 1)]
    Path(tep).write_text("\n".join(phan), encoding="utf-8")
    return Path(tep)


def ngat_dong(chu: str, font: ImageFont.FreeTypeFont, rong_toi_da: int) -> list[str]:
    """Ngắt dòng theo độ rộng điểm ảnh thật của font."""
    dong: list[str] = []
    hien = ""
    for tu in chu.split():
        thu = f"{hien} {tu}".strip()
        if hien and font.getlength(thu) > rong_toi_da:
            dong.append(hien)
            hien = tu
        else:
            hien = thu
    if hien:
        dong.append(hien)
    return dong


def ve_phu_de(
    chu: str,
    rong_khung: int,
    font_path: str | Path,
    co_chu: int,
    mau_chu: str = "#FFFFFF",
    mau_vien: str = "#000000",
    mau_nen: tuple[int, int, int, int] = (0, 0, 0, 150),
) -> Image.Image:
    """Vẽ một khối phụ đề RGBA: chữ to, viền đen, nền bo góc mờ — dễ đọc trên điện thoại ngoài trời."""
    font = ImageFont.truetype(str(font_path), co_chu)
    rong_chu = int(rong_khung * 0.86)
    cac_dong = ngat_dong(chu, font, rong_chu)
    vien = max(2, co_chu // 14)
    cao_dong = int(co_chu * 1.32)
    dem = int(co_chu * 0.45)
    rong = min(rong_khung, int(max(font.getlength(d) for d in cac_dong)) + 2 * dem + 2 * vien)
    cao = cao_dong * len(cac_dong) + 2 * dem
    anh = Image.new("RGBA", (rong, cao), (0, 0, 0, 0))
    ve = ImageDraw.Draw(anh)
    ve.rounded_rectangle((0, 0, rong - 1, cao - 1), radius=int(co_chu * 0.4), fill=mau_nen)
    for k, d in enumerate(cac_dong):
        x = (rong - font.getlength(d)) / 2
        y = dem + k * cao_dong
        ve.text((x, y), d, font=font, fill=mau_chu, stroke_width=vien, stroke_fill=mau_vien)
    return anh
