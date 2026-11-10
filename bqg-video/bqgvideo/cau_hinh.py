"""Đọc cấu hình từ config.toml (+ biến môi trường cho khoá bí mật).

Nguyên tắc an toàn (sửa các lỗ hổng mặc định của bản gốc MoneyPrinterTurbo):
- API chỉ nghe ở 127.0.0.1 mặc định.
- Mở ra mạng (listen_host khác 127.0.0.1/localhost) mà chưa đặt api_key -> TỪ CHỐI khởi động.
- Khoá A.I chỉ lấy từ biến môi trường, không ghi vào tệp cấu hình.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from .brand import GIONG_MAC_DINH, THU_MUC_GOC

DUONG_DAN_MAC_DINH = THU_MUC_GOC / "config.toml"
_LOOPBACK = {"127.0.0.1", "localhost", "::1"}


@dataclass
class CauHinhApp:
    listen_host: str = "127.0.0.1"
    listen_port: int = 8686
    api_key: str = ""
    data_dir: str = "./du-lieu"
    footage_dir: str = "./kho-canh"
    music_dir: str = "./nhac-nen"


@dataclass
class CauHinhLLM:
    # anthropic | ollama | tat (không dùng A.I, chỉ dán kịch bản tay)
    provider: str = "anthropic"
    model: str = "claude-opus-5-5"
    effort: str = "medium"
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:14b"
    timeout_giay: int = 180


@dataclass
class CauHinhThuongHieu:
    hotline: str = ""
    zalo: str = ""  # số Zalo OA hoặc tên OA hiển thị ở cảnh kết
    website: str = ""
    cau_keu_goi: str = "Nhắn Zalo cho Bình Quân: nuôi con gì, bao nhiêu con — kỹ thuật tư vấn đúng máy"
    hien_logo: bool = True


@dataclass
class CauHinhVideo:
    ti_le: str = "9:16"
    fps: int = 30
    co_chu_phu_de: int = 64
    so_ky_tu_toi_da_moi_dong: int = 22
    giay_canh_ket: float = 3.0
    am_luong_nhac: float = 0.12
    giay_toi_da_moi_canh: float = 5.0
    preset_ffmpeg: str = "medium"
    so_luong_ffmpeg: int = 2


@dataclass
class CauHinhGiong:
    giong_mac_dinh: str = GIONG_MAC_DINH
    toc_do: float = 1.0


@dataclass
class CauHinh:
    app: CauHinhApp = field(default_factory=CauHinhApp)
    llm: CauHinhLLM = field(default_factory=CauHinhLLM)
    thuong_hieu: CauHinhThuongHieu = field(default_factory=CauHinhThuongHieu)
    video: CauHinhVideo = field(default_factory=CauHinhVideo)
    giong: CauHinhGiong = field(default_factory=CauHinhGiong)
    goc: Path = THU_MUC_GOC

    # ---- đường dẫn tuyệt đối ----
    def _tuyet_doi(self, p: str) -> Path:
        path = Path(p).expanduser()
        return path if path.is_absolute() else (self.goc / path).resolve()

    @property
    def thu_muc_du_lieu(self) -> Path:
        return self._tuyet_doi(self.app.data_dir)

    @property
    def thu_muc_kho_canh(self) -> Path:
        return self._tuyet_doi(self.app.footage_dir)

    @property
    def thu_muc_nhac(self) -> Path:
        return self._tuyet_doi(self.app.music_dir)

    @property
    def khoa_api(self) -> str:
        return os.environ.get("BQG_VIDEO_API_KEY") or self.app.api_key

    def kiem_tra_an_toan_api(self) -> None:
        """Ném lỗi nếu cấu hình API không an toàn."""
        mo_ra_mang = self.app.listen_host not in _LOOPBACK
        if mo_ra_mang and not self.khoa_api:
            raise RuntimeError(
                "API đang mở ra mạng (listen_host="
                f"{self.app.listen_host}) nhưng chưa đặt api_key. "
                "Đặt BQG_VIDEO_API_KEY hoặc [app].api_key, hoặc để listen_host = 127.0.0.1."
            )
        if self.khoa_api and len(self.khoa_api) < 16:
            raise RuntimeError("api_key quá ngắn — cần tối thiểu 16 ký tự ngẫu nhiên.")


def _ap(obj, du_lieu: dict) -> None:
    for k, v in (du_lieu or {}).items():
        if hasattr(obj, k):
            setattr(obj, k, v)


def doc_cau_hinh(duong_dan: str | Path | None = None) -> CauHinh:
    duong_dan = Path(duong_dan or os.environ.get("BQG_VIDEO_CONFIG") or DUONG_DAN_MAC_DINH)
    ch = CauHinh()
    if duong_dan.exists():
        with open(duong_dan, "rb") as f:
            du_lieu = tomllib.load(f)
        _ap(ch.app, du_lieu.get("app"))
        _ap(ch.llm, du_lieu.get("llm"))
        _ap(ch.thuong_hieu, du_lieu.get("thuong_hieu"))
        _ap(ch.video, du_lieu.get("video"))
        _ap(ch.giong, du_lieu.get("giong"))
        ch.goc = duong_dan.resolve().parent
    return ch
