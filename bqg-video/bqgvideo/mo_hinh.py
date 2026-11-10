"""Cấu trúc dữ liệu dùng chung (kịch bản, yêu cầu dựng, bản ghi video)."""

from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from .brand import DONG_MAY, DONG_MAY_MAC_DINH, GIONG_DOC, GIONG_MAC_DINH, TI_LE_KHUNG


class DoanCanh(BaseModel):
    """Một đoạn lời đọc + thẻ cảnh muốn ghép (khớp với tên tệp trong kho cảnh)."""

    loi: str
    the_canh: list[str] = Field(default_factory=list)


def tach_dong_the(dong: str) -> DoanCanh:
    """'Viên ra đều tay [vien-cam, khuon]' -> DoanCanh(loi='Viên ra đều tay', the_canh=['vien-cam','khuon'])."""
    m = re.search(r"\[([^\]]*)\]\s*$", dong)
    if not m:
        return DoanCanh(loi=dong.strip())
    the = [t.strip() for t in m.group(1).split(",") if t.strip()]
    return DoanCanh(loi=dong[: m.start()].strip(), the_canh=the)


class KichBan(BaseModel):
    chu_de: str = ""
    dong_may: str = DONG_MAY_MAC_DINH
    cau_mo_dau: list[str] = Field(default_factory=list)  # mỗi phần tử = 1 biến thể
    than_bai: list[DoanCanh] = Field(default_factory=list)
    keu_goi: str = ""
    bang_chung: str = ""  # số liệu đã xác minh, dùng để kiểm kịch bản
    nguon: str = "tay"  # tay | anthropic | ollama

    def loi_doc(self, bien_the: int = 0) -> str:
        mo = self.cau_mo_dau[bien_the] if self.cau_mo_dau else ""
        phan = [mo] + [d.loi for d in self.than_bai] + [self.keu_goi]
        return "\n".join(p.strip() for p in phan if p and p.strip())

    def cac_doan(self, bien_the: int = 0) -> list[DoanCanh]:
        """Danh sách đoạn theo thứ tự đọc (câu mở đầu dùng thẻ cảnh của đoạn đầu + 'may-chay')."""
        ds: list[DoanCanh] = []
        if self.cau_mo_dau:
            the_dau = self.than_bai[0].the_canh if self.than_bai else []
            ds.append(DoanCanh(loi=self.cau_mo_dau[bien_the], the_canh=["may-chay", *the_dau]))
        ds.extend(self.than_bai)
        if self.keu_goi.strip():
            ds.append(DoanCanh(loi=self.keu_goi, the_canh=["khach-hang", "nha-xuong"]))
        return ds

    @classmethod
    def tu_van_ban(cls, van_ban: str, **kw) -> "KichBan":
        """Kịch bản tự viết: dòng đầu = câu mở đầu, dòng cuối = kêu gọi, giữa = thân bài.

        Thẻ cảnh có thể ghi cuối dòng trong ngoặc vuông: 'Viên ra đều tay [vien-cam, khuon]'.
        Nhiều câu mở đầu để thử: viết các dòng bắt đầu bằng 'MO:'.
        """
        dong = [d.strip() for d in van_ban.splitlines() if d.strip()]
        mo = [d[3:].strip() for d in dong if d.upper().startswith("MO:")]
        con_lai = [d for d in dong if not d.upper().startswith("MO:")]
        tach_the = tach_dong_the

        if not mo and con_lai:
            mo = [tach_the(con_lai.pop(0)).loi]
        keu_goi = tach_the(con_lai.pop()).loi if len(con_lai) >= 2 else ""
        return cls(cau_mo_dau=mo, than_bai=[tach_the(d) for d in con_lai], keu_goi=keu_goi, **kw)


class YeuCauKichBan(BaseModel):
    chu_de: str
    dong_may: str = DONG_MAY_MAC_DINH
    loi_khach: str = Field("", description="Câu hỏi / nỗi đau thật của khách (đã ẩn danh)")
    bang_chung: str = Field("", description="Số liệu đã xác minh: năng suất, giờ chạy, kết quả khách cũ")
    so_bien_the: int = Field(3, ge=1, le=5)
    thoi_luong_giay: int = Field(45, ge=15, le=120)

    @field_validator("dong_may")
    @classmethod
    def _dong_may_hop_le(cls, v: str) -> str:
        if v not in DONG_MAY:
            raise ValueError(f"Dòng máy không hợp lệ: {v}. Chọn một trong {list(DONG_MAY)}")
        return v


class YeuCauDung(BaseModel):
    kich_ban: KichBan
    so_chu_de: int = Field(1, ge=1, le=99, description="Số thứ tự chủ đề trong ngày — dùng trong mã video")
    cac_bien_the: Optional[list[int]] = None  # None = dựng tất cả biến thể câu mở đầu
    giong: str = GIONG_MAC_DINH
    toc_do: float = Field(1.0, ge=0.7, le=1.5)
    tep_ghi_am: Optional[str] = None  # khi giong = tep-ghi-am
    ti_le: str = "9:16"
    nhac_nen: Optional[str] = None  # tên tệp trong thư mục nhạc nền, None = không nhạc
    phu_de: bool = True

    @field_validator("giong")
    @classmethod
    def _giong(cls, v: str) -> str:
        if v not in GIONG_DOC:
            raise ValueError(f"Giọng không hợp lệ: {v}")
        return v

    @field_validator("ti_le")
    @classmethod
    def _ti_le(cls, v: str) -> str:
        if v not in TI_LE_KHUNG:
            raise ValueError(f"Tỉ lệ khung không hợp lệ: {v}")
        return v


class DoLuong(BaseModel):
    """Số đo từ CRM. None = Chưa có dữ liệu (KHÔNG được hiểu là 0)."""

    luot_xem: Optional[int] = None
    lead: Optional[int] = None
    lead_du_4_cau: Optional[int] = None
    don_may_thuc: Optional[int] = None
    cap_nhat_luc: Optional[str] = None
    nguon_so: Optional[str] = None  # ví dụ: "CRM BQG", "nhập tay — Marketing"


class Duyet(BaseModel):
    nguoi_duyet: str
    dong_y: bool
    checklist: dict[str, bool] = Field(default_factory=dict)
    ghi_chu: str = ""
    luc: Optional[str] = None


class LanDang(BaseModel):
    kenh: str
    lien_ket: str = ""
    luc: Optional[str] = None
    nguoi_dang: str = ""


class BanGhiVideo(BaseModel):
    ma: str
    chu_de: str
    dong_may: str
    bien_the: int
    cau_mo_dau: str
    loi_doc: str
    trang_thai: str = "dang_dung"
    tao_luc: str
    tep_video: Optional[str] = None
    tep_phu_de: Optional[str] = None
    thoi_luong_giay: Optional[float] = None
    giong: str = GIONG_MAC_DINH
    ti_le: str = "9:16"
    canh_da_dung: list[str] = Field(default_factory=list)
    thieu_canh_that: bool = False
    canh_bao: list[dict] = Field(default_factory=list)
    loi: Optional[str] = None
    lich_su_duyet: list[Duyet] = Field(default_factory=list)
    lan_dang: list[LanDang] = Field(default_factory=list)
    do_luong: DoLuong = Field(default_factory=DoLuong)
