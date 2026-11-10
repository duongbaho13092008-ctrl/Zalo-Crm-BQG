import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bqgvideo.cau_hinh import CauHinh  # noqa: E402

CO_FFMPEG = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


@pytest.fixture
def ch(tmp_path: Path) -> CauHinh:
    c = CauHinh()
    c.goc = tmp_path
    c.app.data_dir = "du-lieu"
    c.app.footage_dir = "kho"
    c.app.music_dir = "nhac"
    c.thuong_hieu.hotline = "0912 345 678"
    c.thuong_hieu.zalo = "Bình Quân Group"
    c.video.preset_ffmpeg = "ultrafast"
    c.video.fps = 15
    (tmp_path / "kho").mkdir()
    (tmp_path / "nhac").mkdir()
    return c


def tao_video_gia(tep: Path, giay: float, kich_thuoc: str = "640x360") -> Path:
    tep.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", f"testsrc=size={kich_thuoc}:rate=15",
         "-t", str(giay), str(tep)],
        check=True,
    )
    return tep


def tao_am_gia(tep: Path, giay: float) -> Path:
    tep.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", f"sine=frequency=300:duration={giay}", str(tep)],
        check=True,
    )
    return tep
