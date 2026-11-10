import pytest
from fastapi.testclient import TestClient

from bqgvideo.api import tao_app
from bqgvideo.brand import CHECKLIST_DUYET
from bqgvideo.mo_hinh import BanGhiVideo
from bqgvideo.so_do import SoDo

KHOA = "khoa-thu-nghiem-0123456789"


@pytest.fixture
def client(ch, monkeypatch):
    monkeypatch.delenv("BQG_VIDEO_API_KEY", raising=False)
    ch.app.api_key = KHOA
    return TestClient(tao_app(ch)), ch


def test_can_khoa(client):
    c, _ = client
    assert c.get("/api/v1/suc-khoe").status_code == 200
    assert c.get("/api/v1/videos").status_code == 401
    assert c.get("/api/v1/videos", headers={"X-API-Key": "sai"}).status_code == 401
    assert c.get("/api/v1/videos", headers={"X-API-Key": KHOA}).json() == []


def test_khong_khoi_dong_neu_mo_mang_khong_khoa(ch, monkeypatch):
    monkeypatch.delenv("BQG_VIDEO_API_KEY", raising=False)
    ch.app.listen_host = "0.0.0.0"
    with pytest.raises(RuntimeError):
        tao_app(ch)


def test_kiem_tra_va_chan_duong_dan_tuy_y(client):
    c, _ = client
    h = {"X-API-Key": KHOA}
    r = c.post("/api/v1/kiem-tra", json={"loi_doc": "Máy tốt nhất"}, headers=h).json()
    assert r["canh_bao"][0]["muc"] == "chan"
    r = c.post("/api/v1/videos", headers=h, json={"kich_ban": {"cau_mo_dau": ["a"]}, "giong": "tep-ghi-am",
                                                  "tep_ghi_am": "/etc/passwd"})
    assert r.status_code == 400
    r = c.post("/api/v1/tai-len", headers=h, files={"tep": ("a.exe", b"x")})
    assert r.status_code == 400
    r = c.post("/api/v1/tai-len", headers=h, files={"tep": ("a.mp3", b"x")})
    assert r.status_code == 200 and r.json()["ten_tep"].endswith(".mp3")


def test_duyet_dang_do_luong_qua_api(client):
    c, ch = client
    h = {"X-API-Key": KHOA}
    ma = "V-EPCAM-261110-01A"
    SoDo(ch.thu_muc_du_lieu).luu(BanGhiVideo(ma=ma, chu_de="c", dong_may="may-ep-cam-vien", bien_the=0,
                                             cau_mo_dau="m", loi_doc="m", trang_thai="cho_duyet",
                                             tao_luc="2026-11-10T09:00:00"))
    assert c.post(f"/api/v1/videos/{ma}/dang", headers=h, json={"kenh": "TikTok"}).status_code == 409
    r = c.post(f"/api/v1/videos/{ma}/duyet", headers=h,
               json={"nguoi_duyet": "Lan", "dong_y": True, "checklist": {k: True for k in CHECKLIST_DUYET}})
    assert r.status_code == 200 and r.json()["trang_thai"] == "da_duyet"
    assert c.post(f"/api/v1/videos/{ma}/dang", headers=h, json={"kenh": "TikTok"}).status_code == 200
    r = c.patch(f"/api/v1/videos/{ma}/do-luong", headers=h, json={"lead": 5, "lead_du_4_cau": 2})
    assert r.json()["do_luong"]["lead_du_4_cau"] == 2 and r.json()["do_luong"]["don_may_thuc"] is None
    assert c.patch(f"/api/v1/videos/{ma}/do-luong", headers=h, json={"lead_du_4_cau": 9}).status_code == 422
    assert "Chưa có dữ liệu" in c.get("/api/v1/so-do.csv", headers=h).text
    assert c.get("/api/v1/videos/V-XX/tep/video.mp4", headers=h).status_code == 404
    assert c.get(f"/api/v1/videos/{ma}/tep/ban-ghi.json", headers=h).status_code == 404
