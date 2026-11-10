"""Tìm ffmpeg và đo thời lượng tệp âm thanh / video."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path


class ThieuFFmpeg(RuntimeError):
    pass


def ffmpeg_bin() -> str:
    tim = shutil.which("ffmpeg")
    if tim:
        return tim
    try:  # gói imageio-ffmpeg mang sẵn ffmpeg (tiện cho Windows)
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as e:  # noqa: BLE001
        raise ThieuFFmpeg("Chưa cài ffmpeg. Cài ffmpeg rồi chạy lại.") from e


_THOI_LUONG = re.compile(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)")


def do_thoi_luong(tep: str | Path) -> float | None:
    """Thời lượng (giây) của tệp media; None nếu không đọc được."""
    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        try:
            out = subprocess.run(
                [ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(tep)],
                capture_output=True, text=True, timeout=30, check=True,
            ).stdout.strip()
            return float(out)
        except (OSError, ValueError, subprocess.SubprocessError):
            pass
    try:  # không có ffprobe: đọc dòng "Duration:" của ffmpeg -i
        err = subprocess.run([ffmpeg_bin(), "-hide_banner", "-i", str(tep)], capture_output=True, text=True,
                             timeout=30).stderr
    except (OSError, subprocess.SubprocessError, ThieuFFmpeg):
        return None
    m = _THOI_LUONG.search(err)
    if not m:
        return None
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)
