"""API (cổng kết nối) cho CRM / phần mềm BQG gọi vào: viết kịch bản, dựng video, duyệt, cập nhật số đo.

Bảo mật:
- Có api_key thì MỌI lệnh (trừ /suc-khoe) phải gửi header X-API-Key.
- Không có api_key thì chỉ được nghe ở 127.0.0.1 (kiểm khi khởi động).
- Tệp ghi âm chỉ lấy từ thư mục tải lên của chính phần mềm (chặn đọc tệp tuỳ ý trên máy).
"""

from __future__ import annotations

import hmac
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel

from . import __version__
from .ai_viet import LoiAI
from .cau_hinh import CauHinh, doc_cau_hinh
from .kho_canh import KhoCanh
from .kiem_duyet import kiem_tra
from .mo_hinh import YeuCauDung, YeuCauKichBan
from .quy_trinh import dung_bo_video, so_cho_phep, tao_kich_ban
from .so_do import SoDo

DUOI_AM_THANH = {".mp3", ".wav", ".m4a", ".aac", ".ogg"}
CO_TOI_DA_TAI_LEN = 50 * 1024 * 1024


class YeuCauKiemTra(BaseModel):
    loi_doc: str
    bang_chung: str = ""


class YeuCauDuyet(BaseModel):
    nguoi_duyet: str
    dong_y: bool
    checklist: dict[str, bool] = {}
    ghi_chu: str = ""


class YeuCauDang(BaseModel):
    kenh: str
    lien_ket: str = ""
    nguoi_dang: str = ""


class YeuCauDoLuong(BaseModel):
    luot_xem: Optional[int] = None
    lead: Optional[int] = None
    lead_du_4_cau: Optional[int] = None
    don_may_thuc: Optional[int] = None
    nguon_so: Optional[str] = None


def tao_app(ch: CauHinh | None = None) -> FastAPI:
    ch = ch or doc_cau_hinh()
    ch.kiem_tra_an_toan_api()
    so_do = SoDo(ch.thu_muc_du_lieu)
    thu_muc_tai_len = ch.thu_muc_du_lieu / "tai-len"
    thu_muc_tai_len.mkdir(parents=True, exist_ok=True)
    # dựng video nặng CPU: chạy lần lượt từng việc
    tho = ThreadPoolExecutor(max_workers=1, thread_name_prefix="dung-video")
    viec: dict[str, dict] = {}
    khoa = threading.Lock()

    app = FastAPI(title="Xưởng Video A.I Bình Quân", version=__version__)

    def xac_thuc(x_api_key: str | None = Header(default=None)) -> None:
        khoa_dung = ch.khoa_api
        if not khoa_dung:
            return
        if not x_api_key or not hmac.compare_digest(x_api_key.encode(), khoa_dung.encode()):
            raise HTTPException(401, "Sai hoặc thiếu X-API-Key")

    bao_ve = [Depends(xac_thuc)]

    def _doc(ma: str):
        try:
            return so_do.doc(ma)
        except (KeyError, ValueError) as e:
            raise HTTPException(404, str(e)) from e

    @app.get("/api/v1/suc-khoe")
    def suc_khoe():
        return {"trang_thai": "tot", "phien_ban": __version__}

    @app.get("/api/v1/kho-canh", dependencies=bao_ve)
    def kho_canh():
        kho = KhoCanh(ch.thu_muc_kho_canh)
        return {"tong_canh": len(kho.canh), "theo_dong_may": kho.thong_ke()}

    @app.post("/api/v1/kich-ban", dependencies=bao_ve)
    def viet(yc: YeuCauKichBan):
        try:
            kq = tao_kich_ban(ch, yc)
        except LoiAI as e:
            raise HTTPException(502, str(e)) from e
        return {**kq, "kich_ban": kq["kich_ban"].model_dump()}

    @app.post("/api/v1/kiem-tra", dependencies=bao_ve)
    def kiem(yc: YeuCauKiemTra):
        return {"canh_bao": [c.to_dict() for c in kiem_tra(yc.loi_doc, yc.bang_chung, so_cho_phep(ch))]}

    @app.post("/api/v1/tai-len", dependencies=bao_ve)
    async def tai_len(tep: UploadFile = File(...)):
        duoi = Path(tep.filename or "").suffix.lower()
        if duoi not in DUOI_AM_THANH:
            raise HTTPException(400, f"Chỉ nhận tệp âm thanh {sorted(DUOI_AM_THANH)}")
        du_lieu = await tep.read(CO_TOI_DA_TAI_LEN + 1)
        if len(du_lieu) > CO_TOI_DA_TAI_LEN:
            raise HTTPException(413, "Tệp quá lớn (tối đa 50 MB)")
        ten = f"{uuid.uuid4().hex}{duoi}"
        (thu_muc_tai_len / ten).write_bytes(du_lieu)
        return {"ten_tep": ten}

    def _chay(ma_viec: str, yc: YeuCauDung) -> None:
        def bao(thong_diep: str, phan: float) -> None:
            with khoa:
                viec[ma_viec].update(thong_diep=thong_diep, tien_do=phan)

        with khoa:
            viec[ma_viec]["trang_thai"] = "dang_chay"
        try:
            ds = dung_bo_video(ch, yc, bao)
            with khoa:
                viec[ma_viec].update(trang_thai="xong", videos=[b.ma for b in ds],
                                     loi=[{"ma": b.ma, "loi": b.loi} for b in ds if b.loi])
        except Exception as e:  # noqa: BLE001
            with khoa:
                viec[ma_viec].update(trang_thai="loi", loi=str(e))

    @app.post("/api/v1/videos", dependencies=bao_ve, status_code=202)
    def dung(yc: YeuCauDung):
        if yc.tep_ghi_am:
            ten = Path(yc.tep_ghi_am).name
            if ten != yc.tep_ghi_am or not (thu_muc_tai_len / ten).exists():
                raise HTTPException(400, "tep_ghi_am phải là ten_tep trả về từ /api/v1/tai-len")
            yc = yc.model_copy(update={"tep_ghi_am": str(thu_muc_tai_len / ten)})
        ma_viec = uuid.uuid4().hex[:12]
        with khoa:
            viec[ma_viec] = {"ma_viec": ma_viec, "trang_thai": "cho", "tien_do": 0.0, "thong_diep": "Đang chờ"}
        tho.submit(_chay, ma_viec, yc)
        return {"ma_viec": ma_viec}

    @app.get("/api/v1/viec/{ma_viec}", dependencies=bao_ve)
    def xem_viec(ma_viec: str):
        with khoa:
            if ma_viec not in viec:
                raise HTTPException(404, "Không có việc này")
            return dict(viec[ma_viec])

    @app.get("/api/v1/videos", dependencies=bao_ve)
    def danh_sach(trang_thai: Optional[str] = None):
        return [b.model_dump() for b in so_do.danh_sach(trang_thai)]

    @app.get("/api/v1/videos/{ma}", dependencies=bao_ve)
    def chi_tiet(ma: str):
        return _doc(ma).model_dump()

    @app.get("/api/v1/videos/{ma}/tep/{ten}", dependencies=bao_ve)
    def lay_tep(ma: str, ten: str):
        if ten not in ("video.mp4", "phu-de.srt", "loi-doc.txt"):
            raise HTTPException(404, "Tệp không hợp lệ")
        _doc(ma)
        tep = so_do.thu_muc(ma) / ten
        if not tep.exists():
            raise HTTPException(404, "Chưa có tệp")
        return FileResponse(tep, filename=f"{ma}-{ten}")

    @app.post("/api/v1/videos/{ma}/duyet", dependencies=bao_ve)
    def duyet(ma: str, yc: YeuCauDuyet):
        _doc(ma)
        try:
            return so_do.duyet(ma, yc.nguoi_duyet, yc.checklist, yc.dong_y, yc.ghi_chu).model_dump()
        except ValueError as e:
            raise HTTPException(409, str(e)) from e

    @app.post("/api/v1/videos/{ma}/dang", dependencies=bao_ve)
    def dang(ma: str, yc: YeuCauDang):
        _doc(ma)
        try:
            return so_do.ghi_dang(ma, yc.kenh, yc.lien_ket, yc.nguoi_dang).model_dump()
        except ValueError as e:
            raise HTTPException(409, str(e)) from e

    @app.patch("/api/v1/videos/{ma}/do-luong", dependencies=bao_ve)
    def do_luong(ma: str, yc: YeuCauDoLuong):
        _doc(ma)
        try:
            return so_do.cap_nhat_do_luong(ma, **yc.model_dump(exclude_unset=True)).model_dump()
        except ValueError as e:
            raise HTTPException(422, str(e)) from e

    @app.get("/api/v1/tong-hop", dependencies=bao_ve)
    def tong_hop():
        return so_do.tong_hop_chu_de()

    @app.get("/api/v1/so-do.csv", dependencies=bao_ve, response_class=PlainTextResponse)
    def csv():
        return PlainTextResponse("﻿" + so_do.xuat_csv(), media_type="text/csv; charset=utf-8")

    return app


def chay_api(ch: CauHinh | None = None) -> None:
    import uvicorn

    ch = ch or doc_cau_hinh()
    app = tao_app(ch)
    uvicorn.run(app, host=ch.app.listen_host, port=ch.app.listen_port)
