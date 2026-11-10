import pytest

from bqgvideo.cau_hinh import CauHinh, doc_cau_hinh


def test_mac_dinh_an_toan():
    ch = CauHinh()
    assert ch.app.listen_host == "127.0.0.1"
    ch.kiem_tra_an_toan_api()  # loopback không khoá: được


def test_mo_mang_khong_khoa_bi_chan(monkeypatch):
    monkeypatch.delenv("BQG_VIDEO_API_KEY", raising=False)
    ch = CauHinh()
    ch.app.listen_host = "0.0.0.0"
    with pytest.raises(RuntimeError, match="api_key"):
        ch.kiem_tra_an_toan_api()
    ch.app.api_key = "ngan"
    with pytest.raises(RuntimeError, match="quá ngắn"):
        ch.kiem_tra_an_toan_api()
    monkeypatch.setenv("BQG_VIDEO_API_KEY", "x" * 32)
    ch.kiem_tra_an_toan_api()


def test_doc_tep(tmp_path):
    (tmp_path / "c.toml").write_text('[app]\nlisten_port = 9000\n[thuong_hieu]\nhotline = "1900 1234"\n', "utf-8")
    ch = doc_cau_hinh(tmp_path / "c.toml")
    assert ch.app.listen_port == 9000 and ch.thuong_hieu.hotline == "1900 1234"
    assert ch.thu_muc_du_lieu == (tmp_path / "du-lieu").resolve()
