"""Khâu 1 — A.I viết kịch bản.

Hai nhà cung cấp:
- anthropic: Claude qua Anthropic SDK (cần biến môi trường ANTHROPIC_API_KEY).
- ollama: chạy A.I ngay trên máy BQG, không gửi dữ liệu ra ngoài.

Mọi lời khách đều được ẩn danh (SĐT, email, số dài) TRƯỚC khi gửi đi.
"""

from __future__ import annotations

import json

import requests
from loguru import logger

from .an_danh import an_danh
from .brand import ten_dong_may
from .cau_hinh import CauHinh
from .chi_dan import CHI_DAN_GOC, SO_DO_KICH_BAN, loi_nhan_nguoi_dung
from .mo_hinh import DoanCanh, KichBan, YeuCauKichBan


class LoiAI(RuntimeError):
    pass


def _goi_anthropic(ch: CauHinh, loi_nhan: str) -> dict:
    import anthropic

    client = anthropic.Anthropic(timeout=ch.llm.timeout_giay)
    try:
        # Bật dự phòng phía máy chủ: nếu mô hình chính từ chối, API tự chạy lại trên mô hình dự phòng.
        resp = client.beta.messages.create(
            model=ch.llm.model,
            max_tokens=16000,
            system=CHI_DAN_GOC,
            messages=[{"role": "user", "content": loi_nhan}],
            output_config={
                "effort": ch.llm.effort,
                "format": {"type": "json_schema", "schema": SO_DO_KICH_BAN},
            },
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
    except anthropic.AuthenticationError as e:
        raise LoiAI("Khoá ANTHROPIC_API_KEY sai hoặc chưa đặt.") from e
    except anthropic.RateLimitError as e:
        raise LoiAI("A.I đang quá tải hạn mức — thử lại sau ít phút.") from e
    except anthropic.APIStatusError as e:
        raise LoiAI(f"A.I trả lỗi {e.status_code}: {e.message}") from e
    except anthropic.APIConnectionError as e:
        raise LoiAI("Không kết nối được tới A.I — kiểm tra mạng.") from e

    if resp.stop_reason == "refusal":
        raise LoiAI("A.I từ chối viết kịch bản này — xem lại chủ đề / lời khách.")
    if resp.stop_reason == "max_tokens":
        raise LoiAI("Kịch bản bị cắt giữa chừng — rút ngắn độ dài và thử lại.")
    van_ban = next((b.text for b in resp.content if b.type == "text"), "")
    return json.loads(van_ban)


def _goi_ollama(ch: CauHinh, loi_nhan: str) -> dict:
    try:
        r = requests.post(
            f"{ch.llm.ollama_url.rstrip('/')}/api/chat",
            json={
                "model": ch.llm.ollama_model,
                "stream": False,
                "format": SO_DO_KICH_BAN,
                "messages": [
                    {"role": "system", "content": CHI_DAN_GOC},
                    {"role": "user", "content": loi_nhan},
                ],
            },
            timeout=ch.llm.timeout_giay,
        )
        r.raise_for_status()
    except requests.RequestException as e:
        raise LoiAI(f"Không gọi được Ollama tại {ch.llm.ollama_url}: {e}") from e
    return json.loads(r.json()["message"]["content"])


def viet_kich_ban(ch: CauHinh, yc: YeuCauKichBan, the_trong_kho: list[str]) -> tuple[KichBan, dict[str, int]]:
    """Trả về (kịch bản, thống kê dữ liệu nhạy cảm đã ẩn trước khi gửi A.I)."""
    if ch.llm.provider == "tat":
        raise LoiAI("A.I đang tắt trong cấu hình — hãy dán kịch bản tự viết.")

    loi_khach = an_danh(yc.loi_khach)
    chu_de = an_danh(yc.chu_de)
    bang_chung = an_danh(yc.bang_chung)
    da_an: dict[str, int] = {}
    for kq in (loi_khach, chu_de, bang_chung):
        for k, v in kq.da_an.items():
            da_an[k] = da_an.get(k, 0) + v
    if da_an:
        logger.warning(f"Đã ẩn dữ liệu nhạy cảm trước khi gửi A.I: {da_an}")

    loi_nhan = loi_nhan_nguoi_dung(
        chu_de=chu_de.van_ban,
        ten_dong_may=ten_dong_may(yc.dong_may),
        loi_khach=loi_khach.van_ban,
        bang_chung=bang_chung.van_ban,
        so_bien_the=yc.so_bien_the,
        thoi_luong_giay=yc.thoi_luong_giay,
        the_trong_kho=the_trong_kho,
    )
    if ch.llm.provider == "anthropic":
        du_lieu = _goi_anthropic(ch, loi_nhan)
    elif ch.llm.provider == "ollama":
        du_lieu = _goi_ollama(ch, loi_nhan)
    else:
        raise LoiAI(f"Nhà cung cấp A.I không hỗ trợ: {ch.llm.provider}")

    kb = KichBan(
        chu_de=yc.chu_de,
        dong_may=yc.dong_may,
        cau_mo_dau=[c.strip() for c in du_lieu.get("cau_mo_dau", []) if c.strip()][: yc.so_bien_the],
        than_bai=[DoanCanh(**d) for d in du_lieu.get("than_bai", []) if d.get("loi", "").strip()],
        keu_goi=du_lieu.get("keu_goi", "").strip(),
        bang_chung=yc.bang_chung,
        nguon=ch.llm.provider,
    )
    if not kb.cau_mo_dau or not kb.than_bai:
        raise LoiAI("A.I trả kịch bản thiếu câu mở đầu hoặc thân bài — thử lại.")
    return kb, da_an
