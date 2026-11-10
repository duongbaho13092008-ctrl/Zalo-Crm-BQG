import json
from types import SimpleNamespace

import anthropic
import pytest

from bqgvideo.ai_viet import LoiAI, viet_kich_ban
from bqgvideo.mo_hinh import YeuCauKichBan

TRA_VE = {
    "cau_mo_dau": ["Bà con nuôi cá mà tiền cám ăn hết lãi?", "Một giờ ra 300 kg cám nổi.", "Xem viên cám nổi này."],
    "than_bai": [{"loi": "Đây là máy ép cám viên đang chạy.", "the_canh": ["may-chay"]}],
    "keu_goi": "Nhắn Zalo cho Bình Quân: nuôi cá gì, bao nhiêu ao.",
}


class GiaAnthropic:
    goi: list = []

    def __init__(self, **kw):
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kw):
        GiaAnthropic.goi.append(kw)
        return SimpleNamespace(stop_reason=GiaAnthropic.stop,
                               content=[SimpleNamespace(type="text", text=json.dumps(TRA_VE))])


@pytest.fixture
def gia(monkeypatch):
    GiaAnthropic.goi = []
    GiaAnthropic.stop = "end_turn"
    monkeypatch.setattr(anthropic, "Anthropic", GiaAnthropic)
    return GiaAnthropic


def test_viet_kich_ban_an_danh_truoc_khi_gui(ch, gia):
    yc = YeuCauKichBan(chu_de="Cám nổi", loi_khach="Anh Tư 0912345678 hỏi máy cám nổi",
                       bang_chung="300 kg/giờ", so_bien_the=2)
    kb, da_an = viet_kich_ban(ch, yc, ["may-chay", "vien-cam"])
    goi = gia.goi[0]
    gui_di = goi["messages"][0]["content"]
    assert "0912345678" not in gui_di and "[SĐT đã ẩn]" in gui_di
    assert da_an == {"so_dien_thoai": 1}
    assert goi["model"] == "claude-opus-5-5"
    assert goi["output_config"]["format"]["type"] == "json_schema"
    assert goi["fallbacks"] == "default"
    assert "may-chay, vien-cam" in gui_di
    assert len(kb.cau_mo_dau) == 2 and kb.nguon == "anthropic" and kb.bang_chung == "300 kg/giờ"


def test_tu_choi_thi_bao_loi(ch, gia):
    gia.stop = "refusal"
    with pytest.raises(LoiAI, match="từ chối"):
        viet_kich_ban(ch, YeuCauKichBan(chu_de="x"), [])


def test_ai_tat(ch):
    ch.llm.provider = "tat"
    with pytest.raises(LoiAI):
        viet_kich_ban(ch, YeuCauKichBan(chu_de="x"), [])
