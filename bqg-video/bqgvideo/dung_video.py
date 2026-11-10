"""Khâu 6 — Dựng video bằng ffmpeg: ghép cảnh thật theo kịch bản + giọng + phụ đề + logo + cảnh kết có mã video.

Toàn bộ khâu ghép chạy trong một lệnh ffmpeg (nhanh, chạy được trên máy văn phòng không cần card đồ hoạ).
Python chỉ vẽ các lớp chữ (phụ đề, logo, cảnh kết) thành ảnh PNG trong suốt.
"""

from __future__ import annotations

import random
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from loguru import logger
from PIL import Image, ImageDraw, ImageFont

from .brand import FONT_DAM, FONT_VUA, KHAU_HIEU, LOGO, MAU_CHINH, MAU_NHAN, TEN_CONG_TY, TI_LE_KHUNG
from .cau_hinh import CauHinh
from .kho_canh import Canh
from .media import ffmpeg_bin
from .phu_de import DongPhuDe, ngat_dong, ve_phu_de


@dataclass
class Shot:
    bat_dau: float
    ket_thuc: float
    canh: Canh | None

    @property
    def dai(self) -> float:
        return self.ket_thuc - self.bat_dau


class LoiDung(RuntimeError):
    pass


# ------------------------------------------------------------------ vẽ lớp ảnh


def _hex(m: str) -> tuple[int, int, int]:
    m = m.lstrip("#")
    return tuple(int(m[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _nen_chuyen_mau(rong: int, cao: int) -> Image.Image:
    tren, duoi = np.array(_hex(MAU_CHINH), float), np.array((6, 30, 16), float)
    t = np.linspace(0, 1, cao)[:, None]
    dai = (tren * (1 - t) + duoi * t).astype(np.uint8)
    return Image.fromarray(np.ascontiguousarray(np.repeat(dai[:, None, :], rong, axis=1)))


def _chu_giua(ve: ImageDraw.ImageDraw, y: int, chu: str, font, rong: int, mau) -> int:
    x = (rong - font.getlength(chu)) / 2
    ve.text((x, y), chu, font=font, fill=mau)
    return y + int(font.size * 1.35)


def ve_canh_ket(rong: int, cao: int, ma_video: str, ch: CauHinh) -> Image.Image:
    """Cảnh kết: logo, tên, khẩu hiệu, lời kêu gọi, Zalo/hotline và MÃ VIDEO (để đo lead)."""
    anh = _nen_chuyen_mau(rong, cao).convert("RGBA")
    ve = ImageDraw.Draw(anh)
    don_vi = min(rong, cao)
    y = int(cao * (0.12 if cao > rong else 0.06))
    if LOGO.exists():
        kt = int(don_vi * 0.30)
        logo = Image.open(LOGO).convert("RGBA").resize((kt, kt), Image.LANCZOS)
        anh.alpha_composite(logo, ((rong - kt) // 2, y))
        y += kt + int(don_vi * 0.04)
    f_ten = ImageFont.truetype(str(FONT_DAM), int(don_vi * 0.075))
    f_kh = ImageFont.truetype(str(FONT_VUA), int(don_vi * 0.040))
    f_cta = ImageFont.truetype(str(FONT_DAM), int(don_vi * 0.045))
    y = _chu_giua(ve, y, TEN_CONG_TY.upper(), f_ten, rong, (255, 255, 255))
    y = _chu_giua(ve, y, KHAU_HIEU, f_kh, rong, _hex(MAU_NHAN))
    y += int(don_vi * 0.05)
    for dong in ngat_dong(ch.thuong_hieu.cau_keu_goi, f_cta, int(rong * 0.86)):
        y = _chu_giua(ve, y, dong, f_cta, rong, (255, 255, 255))
    y += int(don_vi * 0.03)
    if ch.thuong_hieu.zalo:
        y = _chu_giua(ve, y, f"Zalo: {ch.thuong_hieu.zalo}", f_cta, rong, _hex(MAU_NHAN))
    if ch.thuong_hieu.hotline:
        y = _chu_giua(ve, y, f"Hotline: {ch.thuong_hieu.hotline}", f_cta, rong, _hex(MAU_NHAN))

    # khung mã video — khách đọc mã này khi nhắn Zalo => quy được lead về đúng video
    y += int(don_vi * 0.04)
    nhan = f"Nhắn mã: {ma_video}"
    co_ma = int(don_vi * 0.060)
    while co_ma > 20 and ImageFont.truetype(str(FONT_DAM), co_ma).getlength(nhan) > rong * 0.80:
        co_ma -= 2
    f_ma = ImageFont.truetype(str(FONT_DAM), co_ma)
    w = int(f_ma.getlength(nhan)) + int(don_vi * 0.08)
    h = int(f_ma.size * 1.6)
    x0 = (rong - w) // 2
    ve.rounded_rectangle((x0, y, x0 + w, y + h), radius=h // 3, fill=_hex(MAU_NHAN))
    _chu_giua(ve, y + int(f_ma.size * 0.22), nhan, f_ma, rong, _hex(MAU_CHINH))
    if ch.thuong_hieu.website:
        _chu_giua(ve, cao - int(don_vi * 0.10), ch.thuong_hieu.website, f_kh, rong, (220, 220, 220))
    return anh.convert("RGB")


def ve_nen_thuong_hieu(rong: int, cao: int, dong_chu: str) -> Image.Image:
    """Cảnh thay thế khi kho chưa có cảnh thật phù hợp (video sẽ bị đánh dấu thiếu cảnh thật)."""
    anh = _nen_chuyen_mau(rong, cao).convert("RGBA")
    kt = int(min(rong, cao) * 0.45)
    if LOGO.exists():
        logo = Image.open(LOGO).convert("RGBA").resize((kt, kt), Image.LANCZOS)
        anh.alpha_composite(logo, ((rong - kt) // 2, int(cao * 0.22)))
    ve = ImageDraw.Draw(anh)
    f = ImageFont.truetype(str(FONT_DAM), int(min(rong, cao) * 0.06))
    for k, dong in enumerate(ngat_dong(dong_chu, f, int(rong * 0.86))):
        _chu_giua(ve, int(cao * 0.22) + kt + int(min(rong, cao) * 0.06) + k * int(f.size * 1.35), dong, f, rong,
                  (255, 255, 255))
    return anh.convert("RGB")


def ve_lop_tren(rong: int, cao: int, ma_video: str, hien_logo: bool) -> Image.Image:
    """Lớp cố định suốt phần thân: logo góc trên trái + mã video góc trên phải (giữ nguồn khi bị đăng lại)."""
    anh = Image.new("RGBA", (rong, cao), (0, 0, 0, 0))
    if hien_logo and LOGO.exists():
        kt = int(min(rong, cao) * 0.13)
        logo = Image.open(LOGO).convert("RGBA").resize((kt, kt), Image.LANCZOS)
        anh.alpha_composite(logo, (int(rong * 0.04), int(cao * 0.035)))
    f_ma = ImageFont.truetype(str(FONT_VUA), int(min(rong, cao) * 0.028))
    w, h = int(f_ma.getlength(ma_video)) + 24, int(f_ma.size * 1.6)
    the = Image.new("RGBA", (w, h), (0, 0, 0, 110))
    ImageDraw.Draw(the).text((12, int(f_ma.size * 0.2)), ma_video, font=f_ma, fill=(255, 255, 255, 230))
    anh.alpha_composite(the, (rong - w - int(rong * 0.04), int(cao * 0.05)))
    return anh


# ------------------------------------------------------------------ lệnh ffmpeg


def _so(x: float) -> str:
    return f"{x:.3f}"


def lenh_ffmpeg(
    shots: list[Shot],
    tep_nen: Path,
    tep_lop_tren: Path,
    phu_de: list[tuple[DongPhuDe, Path, int, int]],
    tep_canh_ket: Path,
    giay_canh_ket: float,
    tep_giong: Path | None,
    tep_nhac: Path | None,
    am_luong_nhac: float,
    thoi_luong_loi: float,
    rong: int,
    cao: int,
    fps: int,
    preset: str,
    so_luong: int,
    tep_ra: Path,
    ngau_nhien: random.Random,
) -> list[str]:
    vao: list[str] = []
    loc: list[str] = []
    so_vao = 0

    def them(*tham_so: str) -> int:
        nonlocal so_vao
        vao.extend(tham_so)
        so_vao += 1
        return so_vao - 1

    chuan = f"setsar=1,fps={fps},format=yuv420p"
    nhan_canh = []
    for k, s in enumerate(shots):
        d = max(0.1, s.dai)
        canh = s.canh
        if canh is None or canh.la_anh:
            anh = tep_nen if canh is None else canh.duong_dan
            i = them("-loop", "1", "-framerate", str(fps), "-t", _so(d), "-i", str(anh))
            du = int(min(rong, cao) * 0.08)
            # lia chậm qua ảnh để ảnh tĩnh có chuyển động
            loc.append(
                f"[{i}:v]scale={rong + du}:{cao + du}:force_original_aspect_ratio=increase,"
                f"crop={rong}:{cao}:x='(iw-{rong})*t/{_so(d)}':y='(ih-{cao})*t/{_so(d)}',"
                f"trim=duration={_so(d)},setpts=PTS-STARTPTS,{chuan}[c{k}]"
            )
        else:
            tl = canh.thoi_luong or 0.0
            if tl >= d + 0.1:
                bd = ngau_nhien.uniform(0, tl - d - 0.05)
                i = them("-ss", _so(bd), "-t", _so(d + 0.05), "-i", str(canh.duong_dan))
            else:  # cảnh ngắn hơn đoạn: lặp lại cảnh
                i = them("-stream_loop", "-1", "-t", _so(d + 0.05), "-i", str(canh.duong_dan))
            loc.append(
                f"[{i}:v]scale={rong}:{cao}:force_original_aspect_ratio=increase,crop={rong}:{cao},"
                f"trim=duration={_so(d)},setpts=PTS-STARTPTS,{chuan}[c{k}]"
            )
        nhan_canh.append(f"[c{k}]")
    loc.append(f"{''.join(nhan_canh)}concat=n={len(nhan_canh)}:v=1:a=0[than0]")

    # lớp logo + mã video, rồi từng dòng phụ đề
    i = them("-i", str(tep_lop_tren))
    loc.append(f"[than0][{i}:v]overlay=0:0:enable='lte(t,{_so(thoi_luong_loi)})'[than1]")
    hien = "than1"
    for k, (d, tep, x, y) in enumerate(phu_de):
        i = them("-i", str(tep))
        loc.append(
            f"[{hien}][{i}:v]overlay={x}:{y}:enable='between(t,{_so(d.bat_dau)},{_so(d.ket_thuc)})'[pd{k}]"
        )
        hien = f"pd{k}"

    i = them("-loop", "1", "-framerate", str(fps), "-t", _so(giay_canh_ket), "-i", str(tep_canh_ket))
    loc.append(f"[{i}:v]scale={rong}:{cao},trim=duration={_so(giay_canh_ket)},setpts=PTS-STARTPTS,{chuan}[ket]")
    loc.append(f"[{hien}]{chuan}[than]")
    loc.append("[than][ket]concat=n=2:v=1:a=0[vra]")

    tong = thoi_luong_loi + giay_canh_ket
    am = []
    if tep_giong:
        i = them("-i", str(tep_giong))
        loc.append(f"[{i}:a]atrim=0:{_so(thoi_luong_loi)},apad,atrim=0:{_so(tong)},aformat=sample_rates=44100:channel_layouts=stereo[giong]")
        am.append("[giong]")
    if tep_nhac:
        i = them("-stream_loop", "-1", "-i", str(tep_nhac))
        loc.append(
            f"[{i}:a]atrim=0:{_so(tong)},volume={am_luong_nhac},"
            f"afade=t=out:st={_so(max(0, tong - 1.5))}:d=1.5,aformat=sample_rates=44100:channel_layouts=stereo[nhac]"
        )
        am.append("[nhac]")
    anh_xa_am: list[str] = []
    if len(am) == 2:
        loc.append("[giong][nhac]amix=inputs=2:duration=first:normalize=0[ara]")
        anh_xa_am = ["-map", "[ara]"]
    elif am:
        anh_xa_am = ["-map", am[0]]

    return [
        ffmpeg_bin(), "-y", "-hide_banner", "-loglevel", "error", *vao,
        "-filter_complex", ";".join(loc),
        "-map", "[vra]", *anh_xa_am,
        "-c:v", "libx264", "-preset", preset, "-crf", "20", "-r", str(fps), "-pix_fmt", "yuv420p",
        *(["-c:a", "aac", "-b:a", "160k"] if anh_xa_am else ["-an"]),
        "-threads", str(so_luong), "-movflags", "+faststart", "-t", _so(tong), str(tep_ra),
    ]


def dung(
    ch: CauHinh,
    shots: list[Shot],
    phu_de: list[DongPhuDe] | None,
    tep_giong: Path | None,
    thoi_luong_loi: float,
    ma_video: str,
    ti_le: str,
    tep_ra: Path,
    tep_nhac: Path | None = None,
    ten_dong_may: str = "",
    seed: int | None = None,
) -> float:
    """Dựng và ghi video. Trả về thời lượng video (giây)."""
    rong, cao = TI_LE_KHUNG[ti_le]
    vc = ch.video
    tep_ra.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=tep_ra.parent, prefix=".tam-") as tam:
        tam = Path(tam)
        tep_nen = tam / "nen.png"
        ve_nen_thuong_hieu(rong, cao, ten_dong_may or TEN_CONG_TY).save(tep_nen)
        tep_lop = tam / "lop-tren.png"
        ve_lop_tren(rong, cao, ma_video, ch.thuong_hieu.hien_logo).save(tep_lop)
        tep_ket = tam / "canh-ket.png"
        ve_canh_ket(rong, cao, ma_video, ch).save(tep_ket)

        lop_pd: list[tuple[DongPhuDe, Path, int, int]] = []
        if phu_de:
            # đặt ở 68% chiều cao khung dọc, tránh thanh nút của TikTok/Reels
            y_tam = 0.68 if cao > rong else 0.80
            co = vc.co_chu_phu_de if cao > rong else int(vc.co_chu_phu_de * 0.8)
            for k, d in enumerate(phu_de):
                if d.bat_dau >= thoi_luong_loi:
                    continue
                anh = ve_phu_de(d.chu, rong, FONT_DAM, co)
                tep = tam / f"pd{k:03d}.png"
                anh.save(tep)
                lop_pd.append((d, tep, (rong - anh.width) // 2, int(cao * y_tam - anh.height / 2)))

        lenh = lenh_ffmpeg(
            shots, tep_nen, tep_lop, lop_pd, tep_ket, vc.giay_canh_ket, tep_giong, tep_nhac, vc.am_luong_nhac,
            thoi_luong_loi, rong, cao, vc.fps, vc.preset_ffmpeg, vc.so_luong_ffmpeg, tep_ra, random.Random(seed),
        )
        logger.info(f"Đang dựng {ma_video} ({rong}x{cao}, {thoi_luong_loi + vc.giay_canh_ket:.1f}s, {len(shots)} cảnh)")
        kq = subprocess.run(lenh, capture_output=True, text=True)
        if kq.returncode != 0:
            raise LoiDung(f"ffmpeg lỗi: {kq.stderr.strip()[-1500:]}")
    return round(thoi_luong_loi + vc.giay_canh_ket, 3)
