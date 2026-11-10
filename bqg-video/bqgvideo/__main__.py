"""Dòng lệnh: python -m bqgvideo <lệnh> ...  (gõ python -m bqgvideo -h để xem hướng dẫn)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .brand import CHECKLIST_DUYET, DONG_MAY, DONG_MAY_MAC_DINH, GIONG_DOC, GIONG_MAC_DINH, TI_LE_KHUNG
from .cau_hinh import doc_cau_hinh
from .kho_canh import KhoCanh
from .kiem_duyet import kiem_tra
from .mo_hinh import KichBan, YeuCauDung, YeuCauKichBan
from .quy_trinh import dung_bo_video, so_cho_phep, tao_kich_ban
from .so_do import CHUA_CO, SoDo, gan_utm


def _in_canh_bao(ds) -> None:
    if not ds:
        print("  ✔ Không có cảnh báo")
    for c in ds:
        c = c if isinstance(c, dict) else c.to_dict()
        nhan = "⛔ CHẶN" if c["muc"] == "chan" else "⚠ XEM LẠI"
        print(f"  {nhan}: {c['noi_dung']}" + (f" — «{c['trich']}»" if c.get("trich") else ""))


def lenh_kho_canh(ch, a) -> None:
    kho = KhoCanh(ch.thu_muc_kho_canh)
    print(f"Kho cảnh: {ch.thu_muc_kho_canh}  ({len(kho.canh)} tệp)")
    for may, tk in kho.thong_ke().items():
        print(f"- {may}: {tk['so_video']} video ({tk['tong_giay']} giây), {tk['so_anh']} ảnh")
        if tk["the"]:
            print(f"    thẻ: {', '.join(tk['the'])}")


def lenh_kich_ban(ch, a) -> None:
    yc = YeuCauKichBan(
        chu_de=a.chu_de, dong_may=a.dong_may, loi_khach=a.loi_khach or "", bang_chung=a.bang_chung or "",
        so_bien_the=a.so_bien_the, thoi_luong_giay=a.thoi_luong,
    )
    kq = tao_kich_ban(ch, yc)
    kb: KichBan = kq["kich_ban"]
    if kq["da_an_truoc_khi_gui_ai"]:
        print(f"Đã ẩn trước khi gửi A.I: {kq['da_an_truoc_khi_gui_ai']}")
    for i, mo in enumerate(kb.cau_mo_dau):
        print(f"\n=== Biến thể {chr(65 + i)} ===\n{kb.loi_doc(i)}")
        _in_canh_bao(kq["canh_bao"][i])
    if a.ra:
        Path(a.ra).write_text(kb.model_dump_json(indent=2), encoding="utf-8")
        print(f"\nĐã lưu kịch bản: {a.ra}")


def _doc_kich_ban(a) -> KichBan:
    tep = Path(a.kich_ban)
    noi_dung = tep.read_text(encoding="utf-8")
    if tep.suffix.lower() == ".json":
        kb = KichBan.model_validate_json(noi_dung)
    else:
        kb = KichBan.tu_van_ban(noi_dung)
    if a.chu_de:
        kb.chu_de = a.chu_de
    if a.dong_may:
        kb.dong_may = a.dong_may
    if a.bang_chung:
        kb.bang_chung = a.bang_chung
    if not kb.chu_de:
        kb.chu_de = tep.stem
    return kb


def lenh_kiem_tra(ch, a) -> None:
    kb = _doc_kich_ban(a)
    for i in range(max(1, len(kb.cau_mo_dau))):
        print(f"Biến thể {chr(65 + i)}:")
        _in_canh_bao(kiem_tra(kb.loi_doc(i), kb.bang_chung, so_cho_phep(ch)))


def lenh_dung(ch, a) -> None:
    kb = _doc_kich_ban(a)
    so_do = SoDo(ch.thu_muc_du_lieu)
    yc = YeuCauDung(
        kich_ban=kb,
        so_chu_de=a.so_chu_de or so_do.tim_so_chu_de_tiep(kb.dong_may),
        cac_bien_the=a.bien_the,
        giong=a.giong,
        toc_do=a.toc_do,
        tep_ghi_am=a.tep_ghi_am,
        ti_le=a.ti_le,
        nhac_nen=a.nhac,
        phu_de=not a.khong_phu_de,
    )
    ds = dung_bo_video(ch, yc, lambda m, p: print(f"  [{p:>4.0%}] {m}"))
    print()
    for b in ds:
        if b.loi:
            print(f"✖ {b.ma}: LỖI — {b.loi}")
            continue
        print(f"✔ {b.ma}: {so_do.thu_muc(b.ma) / 'video.mp4'}  ({b.thoi_luong_giay}s) — CHỜ DUYỆT")
        if b.thieu_canh_that:
            print("   ⚠ Thiếu cảnh thật — có đoạn dùng nền thương hiệu. Bổ sung kho cảnh rồi dựng lại.")
        _in_canh_bao(b.canh_bao)


def lenh_duyet(ch, a) -> None:
    so_do = SoDo(ch.thu_muc_du_lieu)
    if a.da_kiem_het:
        checklist = {k: True for k in CHECKLIST_DUYET}
    else:
        da = set((a.da_kiem or "").split(",")) - {""}
        checklist = {k: k in da for k in CHECKLIST_DUYET}
    bg = so_do.duyet(a.ma, a.nguoi, checklist, not a.tu_choi, a.ghi_chu or "")
    print(f"{bg.ma}: {bg.trang_thai}")


def lenh_dang(ch, a) -> None:
    bg = SoDo(ch.thu_muc_du_lieu).ghi_dang(a.ma, a.kenh, a.lien_ket or "", a.nguoi or "")
    print(f"{bg.ma}: đã ghi nhận đăng {a.kenh}")


def lenh_do_luong(ch, a) -> None:
    so = {k: getattr(a, k) for k in ("luot_xem", "lead", "lead_du_4_cau", "don_may_thuc", "nguon_so")
          if getattr(a, k) is not None}
    bg = SoDo(ch.thu_muc_du_lieu).cap_nhat_do_luong(a.ma, **so)
    print(json.dumps(bg.do_luong.model_dump(), ensure_ascii=False, indent=2))


def lenh_so_do(ch, a) -> None:
    so_do = SoDo(ch.thu_muc_du_lieu)
    if a.csv:
        Path(a.csv).write_text("﻿" + so_do.xuat_csv(), encoding="utf-8")
        print(f"Đã xuất: {a.csv}")
        return
    for nhom in so_do.tong_hop_chu_de():
        print(f"\n■ {nhom['chu_de']} — {nhom['dong_may']}")
        for b in nhom["bien_the"]:
            l4 = CHUA_CO if b["lead_du_4_cau"] is None else b["lead_du_4_cau"]
            don = CHUA_CO if b["don_may_thuc"] is None else b["don_may_thuc"]
            print(f"   {b['ma']} [{b['trang_thai']}] lead đủ 4 câu: {l4} · đơn máy thực: {don}")
            print(f"      mở đầu: {b['cau_mo_dau']}")


def lenh_api(ch, a) -> None:
    from .api import chay_api

    chay_api(ch)


def lenh_utm(ch, a) -> None:
    print(gan_utm(a.lien_ket, a.ma, a.kenh))


def tao_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="bqgvideo", description="Xưởng Video A.I Bình Quân")
    p.add_argument("--cau-hinh", help="Đường dẫn config.toml")
    sub = p.add_subparsers(dest="lenh", required=True)

    sub.add_parser("kho-canh", help="Xem kho cảnh thật theo dòng máy").set_defaults(f=lenh_kho_canh)

    k = sub.add_parser("kich-ban", help="A.I viết kịch bản nhiều biến thể câu mở đầu")
    k.add_argument("--chu-de", required=True)
    k.add_argument("--dong-may", default=DONG_MAY_MAC_DINH, choices=list(DONG_MAY))
    k.add_argument("--loi-khach", help="Câu hỏi / nỗi đau thật của khách")
    k.add_argument("--bang-chung", help="Số liệu đã xác minh")
    k.add_argument("--so-bien-the", type=int, default=3)
    k.add_argument("--thoi-luong", type=int, default=45)
    k.add_argument("--ra", help="Lưu kịch bản ra tệp .json")
    k.set_defaults(f=lenh_kich_ban)

    def them_kich_ban(sp):
        sp.add_argument("--kich-ban", required=True, help="Tệp .json (từ lệnh kich-ban) hoặc .txt tự viết")
        sp.add_argument("--chu-de")
        sp.add_argument("--dong-may", choices=list(DONG_MAY))
        sp.add_argument("--bang-chung")

    kt = sub.add_parser("kiem-tra", help="Kiểm kịch bản: hứa quá, số liệu chưa có bằng chứng, dữ liệu khách")
    them_kich_ban(kt)
    kt.set_defaults(f=lenh_kiem_tra)

    d = sub.add_parser("dung", help="Dựng video (mọi biến thể câu mở đầu)")
    them_kich_ban(d)
    d.add_argument("--so-chu-de", type=int, help="Số chủ đề trong ngày (mặc định: tự tăng)")
    d.add_argument("--bien-the", type=int, nargs="*", help="Chỉ dựng các biến thể này (0=A, 1=B...)")
    d.add_argument("--giong", default=GIONG_MAC_DINH, choices=list(GIONG_DOC))
    d.add_argument("--toc-do", type=float, default=1.0)
    d.add_argument("--tep-ghi-am")
    d.add_argument("--ti-le", default="9:16", choices=list(TI_LE_KHUNG))
    d.add_argument("--nhac", help="Tên tệp nhạc trong thư mục nhạc nền")
    d.add_argument("--khong-phu-de", action="store_true")
    d.set_defaults(f=lenh_dung)

    du = sub.add_parser("duyet", help="Duyệt hoặc từ chối video")
    du.add_argument("ma")
    du.add_argument("--nguoi", required=True)
    du.add_argument("--da-kiem", help=f"Các mục đã kiểm, cách nhau dấu phẩy: {','.join(CHECKLIST_DUYET)}")
    du.add_argument("--da-kiem-het", action="store_true", help="Đã kiểm đủ mọi mục")
    du.add_argument("--tu-choi", action="store_true")
    du.add_argument("--ghi-chu")
    du.set_defaults(f=lenh_duyet)

    dg = sub.add_parser("dang", help="Ghi nhận đã đăng (chỉ video đã duyệt)")
    dg.add_argument("ma")
    dg.add_argument("--kenh", required=True)
    dg.add_argument("--lien-ket")
    dg.add_argument("--nguoi")
    dg.set_defaults(f=lenh_dang)

    dl = sub.add_parser("do-luong", help="Cập nhật số đo từ CRM")
    dl.add_argument("ma")
    for ten in ("luot-xem", "lead", "lead-du-4-cau", "don-may-thuc"):
        dl.add_argument(f"--{ten}", type=int, dest=ten.replace("-", "_"))
    dl.add_argument("--nguon-so")
    dl.set_defaults(f=lenh_do_luong)

    sd = sub.add_parser("so-do", help="Xem sổ đo theo chủ đề / xuất CSV")
    sd.add_argument("--csv")
    sd.set_defaults(f=lenh_so_do)

    u = sub.add_parser("utm", help="Gắn mã video vào link website")
    u.add_argument("lien_ket")
    u.add_argument("ma")
    u.add_argument("kenh")
    u.set_defaults(f=lenh_utm)

    sub.add_parser("api", help="Chạy API cho CRM gọi vào").set_defaults(f=lenh_api)
    return p


def main(argv: list[str] | None = None) -> int:
    a = tao_parser().parse_args(argv)
    ch = doc_cau_hinh(a.cau_hinh)
    try:
        a.f(ch, a)
    except (ValueError, KeyError, RuntimeError) as e:
        print(f"Lỗi: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
