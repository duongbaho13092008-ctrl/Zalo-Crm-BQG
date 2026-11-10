"""Kiểm thử tích hợp: dựng video thật bằng ffmpeg với cảnh giả lập."""

import json
import subprocess

import pytest

from bqgvideo.mo_hinh import KichBan, YeuCauDung
from bqgvideo.quy_trinh import dung_bo_video
from conftest import CO_FFMPEG, tao_am_gia, tao_video_gia

pytestmark = pytest.mark.skipif(not CO_FFMPEG, reason="cần ffmpeg + ffprobe")

KB = KichBan.tu_van_ban(
    """MO: Bà con nuôi cá mà tiền cám ăn hết lãi?
MO: Một giờ ra 300 kg cám nổi.
Đây là máy ép cám viên đang chạy. [may-chay, vien-cam]
Viên ra đều, nổi lâu trên mặt nước. [khuon]
Bà con nhắn Zalo cho Bình Quân.""",
    chu_de="Cám nổi", dong_may="may-ep-cam-vien", bang_chung="300 kg/giờ",
)


def thong_tin(tep):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height:format=duration",
                          "-of", "json", str(tep)], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def test_dung_khong_giong_va_tep_ghi_am(ch):
    kho = ch.thu_muc_kho_canh
    tao_video_gia(kho / "may-ep-cam-vien" / "may-chay_vien-cam_01.mp4", 6)
    tao_video_gia(kho / "may-ep-cam-vien" / "khuon_02.mp4", 1.5, "360x640")  # ngắn hơn đoạn => phải lặp
    (kho / "chung").mkdir()
    subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=orange:size=400x300",
                    "-frames:v", "1", str(kho / "chung" / "nha-xuong_01.jpg")], check=True)
    tao_am_gia(ch.thu_muc_nhac / "nhac.mp3", 3)

    ds = dung_bo_video(ch, YeuCauDung(kich_ban=KB, so_chu_de=7, giong="khong-giong", nhac_nen="nhac.mp3"))
    assert [b.trang_thai for b in ds] == ["cho_duyet", "cho_duyet"], [b.loi for b in ds]
    assert [b.ma[-3:] for b in ds] == ["07A", "07B"]
    tt = thong_tin(ch.thu_muc_du_lieu / "videos" / ds[0].ma / "video.mp4")
    video = next(s for s in tt["streams"] if s["codec_type"] == "video")
    assert (video["width"], video["height"]) == (1080, 1920)
    assert any(s["codec_type"] == "audio" for s in tt["streams"])
    assert abs(float(tt["format"]["duration"]) - ds[0].thoi_luong_giay) < 0.3
    assert not ds[0].thieu_canh_that
    assert all("may-ep-cam-vien/" in c or "chung/" in c for c in ds[0].canh_da_dung)
    assert ds[1].canh_bao == []  # 300 kg có trong bằng chứng

    am = tao_am_gia(ch.goc / "ghi-am.mp3", 9)
    ds = dung_bo_video(ch, YeuCauDung(kich_ban=KB, so_chu_de=8, giong="tep-ghi-am", tep_ghi_am=str(am),
                                      cac_bien_the=[1], ti_le="16:9"))
    assert ds[0].trang_thai == "cho_duyet", ds[0].loi
    tt = thong_tin(ch.thu_muc_du_lieu / "videos" / ds[0].ma / "video.mp4")
    video = next(s for s in tt["streams"] if s["codec_type"] == "video")
    assert (video["width"], video["height"]) == (1920, 1080)
    assert abs(float(tt["format"]["duration"]) - (9 + ch.video.giay_canh_ket)) < 0.3


def test_kho_trong_van_dung_nhung_danh_dau(ch):
    ds = dung_bo_video(ch, YeuCauDung(kich_ban=KB, so_chu_de=9, giong="khong-giong", cac_bien_the=[0], ti_le="1:1"))
    assert ds[0].trang_thai == "cho_duyet" and ds[0].thieu_canh_that


def test_mot_tep_ghi_am_chi_mot_bien_the(ch):
    with pytest.raises(ValueError, match="1 biến thể"):
        dung_bo_video(ch, YeuCauDung(kich_ban=KB, giong="tep-ghi-am", tep_ghi_am="x.mp3"))


def test_ma_trung_khong_ghi_de(ch):
    dung_bo_video(ch, YeuCauDung(kich_ban=KB, so_chu_de=11, giong="khong-giong", cac_bien_the=[0], ti_le="1:1"))
    with pytest.raises(ValueError, match="đã có video"):
        dung_bo_video(ch, YeuCauDung(kich_ban=KB, so_chu_de=11, giong="khong-giong", cac_bien_the=[0], ti_le="1:1"))

