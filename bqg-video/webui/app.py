"""Giao diện web tiếng Việt — Xưởng Video A.I Bình Quân.

Chạy:  streamlit run webui/app.py   (xem README.md)
"""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bqgvideo import __version__  # noqa: E402
from bqgvideo.ai_viet import LoiAI  # noqa: E402
from bqgvideo.brand import (  # noqa: E402
    BON_CAU_LOC,
    CHECKLIST_DUYET,
    DONG_MAY,
    GIONG_DOC,
    KENH_DANG,
    KHAU_HIEU,
    KIEU_CAU_MO_DAU,
    LOGO,
    MAU_CHINH,
    TI_LE_KHUNG,
    TRANG_THAI,
    ten_dong_may,
)
from bqgvideo.cau_hinh import doc_cau_hinh  # noqa: E402
from bqgvideo.kho_canh import DUOI_ANH, DUOI_VIDEO, KhoCanh  # noqa: E402
from bqgvideo.kiem_duyet import co_loi_chan  # noqa: E402
from bqgvideo.mo_hinh import KichBan, YeuCauDung, YeuCauKichBan, tach_dong_the  # noqa: E402
from bqgvideo.quy_trinh import dung_bo_video, kiem_kich_ban, tao_kich_ban  # noqa: E402
from bqgvideo.so_do import CHUA_CO, SoDo, gan_utm  # noqa: E402
from bqgvideo.van_ban import slug  # noqa: E402

st.set_page_config(page_title="Xưởng Video A.I Bình Quân", page_icon=str(LOGO), layout="wide")
st.markdown(
    f"""<style>
    h1,h2,h3{{color:{MAU_CHINH}}}
    @media (prefers-color-scheme: dark){{h1,h2,h3{{color:#7BD88F}}}}
    </style>""",
    unsafe_allow_html=True,
)

ch = doc_cau_hinh()
so_do = SoDo(ch.thu_muc_du_lieu)
TEN_BIEN_THE = "ABCDE"


def hien_canh_bao(ds: list[dict]) -> None:
    if not ds:
        st.success("Không có cảnh báo.", icon="✅")
    for c in ds:
        trich = f" — «{c['trich']}»" if c.get("trich") else ""
        if c["muc"] == "chan":
            st.error(f"CHẶN: {c['noi_dung']}{trich}", icon="⛔")
        else:
            st.warning(f"XEM LẠI: {c['noi_dung']}{trich}", icon="⚠️")


def so_hien(v) -> str:
    return CHUA_CO if v is None else str(v)


# ------------------------------------------------------------------ thanh bên
with st.sidebar:
    st.image(str(LOGO), width=110)
    st.markdown(f"### Xưởng Video A.I\n**Bình Quân Group**  \n_{KHAU_HIEU}_")
    st.caption(f"Phiên bản {__version__}")
    st.divider()
    if ch.llm.provider == "anthropic":
        co_khoa = bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))
        st.markdown(f"**A.I viết kịch bản:** Claude (`{ch.llm.model}`)")
        if not co_khoa:
            st.warning("Chưa đặt khoá ANTHROPIC_API_KEY — chỉ dùng được kịch bản tự viết.")
    elif ch.llm.provider == "ollama":
        st.markdown(f"**A.I viết kịch bản:** Ollama trên máy (`{ch.llm.ollama_model}`) — không gửi dữ liệu ra ngoài")
    else:
        st.markdown("**A.I viết kịch bản:** đang tắt")
    st.markdown(f"**Kho cảnh:** `{ch.thu_muc_kho_canh}`")
    cho = len(so_do.danh_sach("cho_duyet"))
    st.metric("Video chờ duyệt", cho)
    st.divider()
    st.caption("Video đo bằng **lead đủ 4 câu lọc** và **đơn máy thực**, không đo bằng lượt xem.")
    for i, c in enumerate(BON_CAU_LOC, 1):
        st.caption(f"{i}. {c}")

tab_kb, tab_dung, tab_duyet, tab_do, tab_kho = st.tabs(
    ["① Kịch bản", "② Dựng video", "③ Duyệt", "④ Đăng & đo lead", "Kho cảnh thật"]
)

# ------------------------------------------------------------------ ① kịch bản
with tab_kb:
    st.subheader("Kịch bản từ lời khách thật")
    st.caption(
        "Lấy câu hỏi / nỗi đau thật từ Zalo, cuộc gọi (đã bỏ tên, SĐT). Mỗi chủ đề ra nhiều biến thể — "
        "**chỉ đổi câu mở đầu**, thân bài giữ nguyên để so được câu nào hút lead hơn."
    )
    c1, c2 = st.columns(2)
    with c1:
        chu_de = st.text_input("Chủ đề", placeholder="VD: Tự làm cám nổi cho ao cá, đỡ tiền cám")
        dong_may = st.selectbox("Dòng máy", list(DONG_MAY), format_func=ten_dong_may)
        loi_khach = st.text_area("Lời khách thật (đã ẩn danh)", height=110,
                                 placeholder="VD: Nuôi 3 ao cá trắm, mỗi tháng tiền cám hơn chục triệu, tự làm có lợi không?")
    with c2:
        bang_chung = st.text_area("Bằng chứng đã xác minh (số liệu được phép nói)", height=110,
                                  placeholder="VD: Máy ép cám nổi tại trại khách cũ ở Hải Dương chạy 300 kg/giờ, kỹ thuật BQG đo ngày 05/11")
        so_bien_the = st.slider("Số biến thể câu mở đầu", 1, 5, 3)
        thoi_luong = st.slider("Độ dài video (giây)", 15, 90, 45, step=5)
        st.caption("Kiểu câu mở đầu: " + " · ".join(KIEU_CAU_MO_DAU))

    b1, b2 = st.columns(2)
    if b1.button("✨ A.I viết kịch bản", type="primary", disabled=not chu_de):
        try:
            with st.spinner("A.I đang viết..."):
                kq = tao_kich_ban(ch, YeuCauKichBan(chu_de=chu_de, dong_may=dong_may, loi_khach=loi_khach,
                                                    bang_chung=bang_chung, so_bien_the=so_bien_the,
                                                    thoi_luong_giay=thoi_luong))
            st.session_state["kich_ban"] = kq["kich_ban"]
            if kq["da_an_truoc_khi_gui_ai"]:
                st.info(f"Đã ẩn dữ liệu nhạy cảm trước khi gửi A.I: {kq['da_an_truoc_khi_gui_ai']}")
        except LoiAI as e:
            st.error(str(e))
    with b2.expander("✍️ Hoặc dán kịch bản tự viết"):
        st.caption("Mỗi dòng một câu. Dòng bắt đầu `MO:` là câu mở đầu (mỗi dòng = 1 biến thể). Dòng cuối là "
                   "câu kêu gọi. Thẻ cảnh ghi cuối dòng: `Viên ra đều tay [vien-cam, khuon]`.")
        tu_viet = st.text_area("Kịch bản", height=180, key="tu_viet")
        if st.button("Dùng kịch bản này", disabled=not tu_viet.strip()):
            st.session_state["kich_ban"] = KichBan.tu_van_ban(
                tu_viet, chu_de=chu_de or "Chủ đề tự viết", dong_may=dong_may, bang_chung=bang_chung)

    kb: KichBan | None = st.session_state.get("kich_ban")
    if kb:
        st.divider()
        st.markdown(f"#### Sửa kịch bản — {kb.chu_de} · {ten_dong_may(kb.dong_may)}")
        mo_moi = []
        for i, mo in enumerate(kb.cau_mo_dau):
            mo_moi.append(st.text_input(f"Câu mở đầu biến thể {TEN_BIEN_THE[i]}", mo, key=f"mo_{i}_{id(kb)}"))
        than = "\n".join(f"{d.loi} [{', '.join(d.the_canh)}]" if d.the_canh else d.loi for d in kb.than_bai)
        than_moi = st.text_area("Thân bài (dùng chung) — thẻ cảnh trong [ ]", than, height=200, key=f"than_{id(kb)}")
        keu_goi = st.text_input("Câu kêu gọi", kb.keu_goi, key=f"kg_{id(kb)}")
        bc_moi = st.text_input("Bằng chứng đã xác minh", kb.bang_chung, key=f"bc_{id(kb)}")
        than_bai = [tach_dong_the(d) for d in than_moi.splitlines() if d.strip()]
        kb_moi = kb.model_copy(update={"cau_mo_dau": [m for m in mo_moi if m.strip()], "than_bai": than_bai,
                                       "keu_goi": keu_goi, "bang_chung": bc_moi})
        st.session_state["kich_ban"] = kb_moi
        st.markdown("##### Kiểm kịch bản")
        for i, cb in enumerate(kiem_kich_ban(ch, kb_moi)):
            with st.expander(f"Biến thể {TEN_BIEN_THE[i]} — {len(cb)} cảnh báo", expanded=bool(cb)):
                st.text(kb_moi.loi_doc(i))
                hien_canh_bao(cb)
        st.download_button("Tải kịch bản (.json)", kb_moi.model_dump_json(indent=2),
                           file_name=f"kich-ban-{slug(kb_moi.chu_de)[:40]}.json")

# ------------------------------------------------------------------ ② dựng
with tab_dung:
    kb = st.session_state.get("kich_ban")
    if not kb:
        st.info("Làm kịch bản ở thẻ ① trước.")
    else:
        st.subheader(f"Dựng: {kb.chu_de}")
        cb_tong = kiem_kich_ban(ch, kb)
        c1, c2, c3 = st.columns(3)
        with c1:
            giong = st.selectbox("Giọng đọc", list(GIONG_DOC), format_func=GIONG_DOC.get)
            toc_do = st.slider("Tốc độ đọc", 0.8, 1.3, ch.giong.toc_do, 0.05)
            tep_ghi_am = None
            if giong == "tep-ghi-am":
                tl = st.file_uploader("Tệp ghi âm (đọc đúng lời của 1 biến thể)", type=["mp3", "wav", "m4a"])
                if tl:
                    thu_muc = ch.thu_muc_du_lieu / "tai-len"
                    thu_muc.mkdir(parents=True, exist_ok=True)
                    du_lieu = tl.getvalue()
                    tep = thu_muc / f"{hashlib.sha1(du_lieu).hexdigest()[:16]}{Path(tl.name).suffix.lower()}"
                    if not tep.exists():
                        tep.write_bytes(du_lieu)
                    tep_ghi_am = str(tep)
        with c2:
            ti_le = st.selectbox("Khung hình", list(TI_LE_KHUNG), help="9:16 cho TikTok / Reels / Shorts")
            nhac_co = sorted(p.name for p in ch.thu_muc_nhac.glob("*") if p.suffix.lower() in {".mp3", ".wav", ".m4a"}) \
                if ch.thu_muc_nhac.exists() else []
            nhac = st.selectbox("Nhạc nền", [None, *nhac_co], format_func=lambda x: "Không nhạc" if x is None else x)
            st.caption("Chỉ dùng nhạc BQG có quyền sử dụng — nhạc có bản quyền dễ bị TikTok tắt tiếng.")
            phu_de = st.checkbox("Phụ đề chữ to (Be Vietnam Pro)", True)
        with c3:
            so_bt = max(1, len(kb.cau_mo_dau))
            mac_dinh = [0] if giong == "tep-ghi-am" else list(range(so_bt))
            bien_the = st.multiselect("Biến thể cần dựng", list(range(so_bt)), mac_dinh,
                                      format_func=lambda i: f"{TEN_BIEN_THE[i]}: {kb.cau_mo_dau[i][:40]}" if kb.cau_mo_dau else "A")
            so_chu_de = st.number_input("Số chủ đề trong ngày (trong mã video)", 1, 99,
                                        so_do.tim_so_chu_de_tiep(kb.dong_may))
        if any(co_loi_chan(cb_tong[i]) for i in bien_the if i < len(cb_tong)):
            st.error("Kịch bản còn lỗi CHẶN — video dựng ra sẽ không duyệt được. Sửa ở thẻ ① trước.", icon="⛔")
        if st.button("🎬 Dựng video", type="primary", disabled=not bien_the):
            thanh = st.progress(0.0, "Bắt đầu...")
            try:
                ds = dung_bo_video(
                    ch,
                    YeuCauDung(kich_ban=kb, so_chu_de=int(so_chu_de), cac_bien_the=bien_the, giong=giong,
                               toc_do=toc_do, tep_ghi_am=tep_ghi_am, ti_le=ti_le, nhac_nen=nhac, phu_de=phu_de),
                    lambda m, p: thanh.progress(min(1.0, p), m),
                )
            except ValueError as e:
                st.error(str(e))
                ds = []
            for b in ds:
                if b.loi:
                    st.error(f"{b.ma}: {b.loi}")
                    continue
                st.success(f"{b.ma} — xong, đang CHỜ DUYỆT ({b.thoi_luong_giay}s)")
                if b.thieu_canh_that:
                    st.warning("Có đoạn thiếu cảnh thật, đang dùng nền thương hiệu. Bổ sung kho cảnh rồi dựng lại.")
                st.video(str(so_do.thu_muc(b.ma) / "video.mp4"))

# ------------------------------------------------------------------ ③ duyệt
with tab_duyet:
    st.subheader("Duyệt rồi mới đăng")
    st.caption("Phần mềm KHÔNG tự đăng. Người duyệt tích đủ danh mục kiểm thì video mới được đăng.")
    ds = so_do.danh_sach("cho_duyet") + so_do.danh_sach("tu_choi")
    if not ds:
        st.info("Không có video chờ duyệt.")
    for b in ds:
        with st.expander(f"{b.ma} · {b.chu_de} · {TRANG_THAI[b.trang_thai]}", expanded=b.trang_thai == "cho_duyet"):
            c1, c2 = st.columns([2, 3])
            with c1:
                tep = so_do.thu_muc(b.ma) / "video.mp4"
                if tep.exists():
                    st.video(str(tep))
            with c2:
                st.markdown(f"**Câu mở đầu:** {b.cau_mo_dau}")
                st.text(b.loi_doc)
                hien_canh_bao(b.canh_bao)
                if b.thieu_canh_that:
                    st.warning("Có đoạn thiếu cảnh thật (nền thương hiệu).")
                with st.popover("Cảnh đã dùng"):
                    st.write(b.canh_da_dung)
                for d in b.lich_su_duyet:
                    st.caption(f"{d.luc} · {d.nguoi_duyet}: {'Đồng ý' if d.dong_y else 'Từ chối'} {d.ghi_chu}")
                with st.form(f"duyet_{b.ma}"):
                    tich = {k: st.checkbox(v, key=f"{b.ma}_{k}") for k, v in CHECKLIST_DUYET.items()}
                    nguoi = st.text_input("Người duyệt", key=f"{b.ma}_nguoi")
                    ghi_chu = st.text_input("Ghi chú / lý do từ chối", key=f"{b.ma}_gc")
                    d1, d2 = st.columns(2)
                    dong_y = d1.form_submit_button("✅ Duyệt", type="primary")
                    tu_choi = d2.form_submit_button("↩️ Từ chối")
                    if dong_y or tu_choi:
                        try:
                            so_do.duyet(b.ma, nguoi, tich, dong_y, ghi_chu)
                            st.success("Đã lưu.")
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))

# ------------------------------------------------------------------ ④ đăng & đo
with tab_do:
    st.subheader("So các biến thể theo lead đủ 4 câu lọc và đơn máy thực")
    st.caption("Sales ghi MÃ VIDEO vào trường nguồn của khách trên CRM. Ô trống = Chưa có dữ liệu (không phải 0). "
               "Ngưỡng giữ / bỏ biến thể do Sếp chốt — phần mềm không tự kết luận.")
    nhom = so_do.tong_hop_chu_de()
    if not nhom:
        st.info("Chưa có video.")
    for n in nhom:
        st.markdown(f"**{n['chu_de']}** — {n['dong_may']}" + ("" if n["du_du_lieu"] else f"  ·  _{CHUA_CO} đủ để so_"))
        st.dataframe(
            [{"Mã": b["ma"], "Câu mở đầu": b["cau_mo_dau"], "Trạng thái": TRANG_THAI.get(b["trang_thai"]),
              "Lead đủ 4 câu": so_hien(b["lead_du_4_cau"]), "Đơn máy thực": so_hien(b["don_may_thuc"])}
             for b in n["bien_the"]],
            hide_index=True, width="stretch",
        )
    st.download_button("⬇️ Tải sổ đo (CSV, mở bằng Excel)", "﻿" + so_do.xuat_csv(), "so-do-video-bqg.csv")

    st.divider()
    da_duyet = so_do.danh_sach("da_duyet") + so_do.danh_sach("da_dang")
    if da_duyet:
        ma = st.selectbox("Chọn video", [b.ma for b in da_duyet])
        b = so_do.doc(ma)
        c1, c2 = st.columns(2)
        with c1, st.form("dang"):
            st.markdown("**Ghi nhận đã đăng**")
            kenh = st.selectbox("Kênh", KENH_DANG)
            lien_ket = st.text_input("Liên kết bài đăng")
            nguoi_dang = st.text_input("Người đăng")
            if st.form_submit_button("Lưu"):
                so_do.ghi_dang(ma, kenh, lien_ket, nguoi_dang)
                st.rerun()
            for d in b.lan_dang:
                st.caption(f"{d.luc} · {d.kenh} · {d.lien_ket}")
        with c2, st.form("do"):
            st.markdown("**Số đo từ CRM** (để trống nếu chưa có)")
            dl = b.do_luong

            def o(nhan, gt):
                v = st.text_input(nhan, "" if gt is None else str(gt))
                return int(v) if v.strip().isdigit() else None

            vals = {"luot_xem": o("Lượt xem", dl.luot_xem), "lead": o("Lead (tổng liên hệ)", dl.lead),
                    "lead_du_4_cau": o("Lead đủ 4 câu lọc", dl.lead_du_4_cau),
                    "don_may_thuc": o("Đơn máy thực (đã giao, nghiệm thu, thu đủ)", dl.don_may_thuc)}
            nguon = st.text_input("Nguồn số", dl.nguon_so or "CRM BQG")
            if st.form_submit_button("Lưu số đo"):
                try:
                    so_do.cap_nhat_do_luong(ma, **vals, nguon_so=nguon)
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
        st.markdown("**Gắn mã video vào link website** (đo nguồn khi khách bấm link)")
        u1, u2 = st.columns([3, 1])
        lk = u1.text_input("Link website / trang sản phẩm", placeholder="https://...")
        kenh_utm = u2.selectbox("Kênh đăng", KENH_DANG, key="kenh_utm")
        if lk:
            st.code(gan_utm(lk, ma, kenh_utm))

# ------------------------------------------------------------------ kho cảnh
with tab_kho:
    st.subheader("Kho cảnh thật của BQG")
    st.caption("Video BQG phải là máy BQG chạy thật. Quay 30–50 đoạn 5–10 giây: máy chạy, viên cám ra, "
               "khách cầm viên cám, nhà xưởng. Đặt đúng dòng máy và thẻ để phần mềm khớp cảnh theo kịch bản.")
    kho = KhoCanh(ch.thu_muc_kho_canh)
    st.dataframe(
        [{"Dòng máy": ten_dong_may(k), "Video": v["so_video"], "Giây": v["tong_giay"], "Ảnh": v["so_anh"],
          "Thẻ": ", ".join(v["the"])} for k, v in kho.thong_ke().items()],
        hide_index=True, width="stretch",
    )
    with st.form("tai_canh", clear_on_submit=True):
        st.markdown("**Thêm cảnh vào kho** — phần mềm tự đặt tên tệp đúng quy ước")
        may = st.selectbox("Dòng máy", list(DONG_MAY), format_func=ten_dong_may)
        st.caption("Thẻ gợi ý: " + ", ".join(DONG_MAY[may].the_goi_y))
        the = st.text_input("Thẻ cảnh, cách nhau dấu phẩy", placeholder="may chay, vien cam, khuon 6 ly")
        tep = st.file_uploader("Tệp video / ảnh", type=[d.strip(".") for d in DUOI_VIDEO | DUOI_ANH],
                               accept_multiple_files=True)
        if st.form_submit_button("Lưu vào kho") and tep:
            thu_muc = ch.thu_muc_kho_canh / may
            thu_muc.mkdir(parents=True, exist_ok=True)
            ds_the = [slug(t) for t in the.split(",") if slug(t)] or ["may-chay"]
            for f in tep:
                so = len(list(thu_muc.glob("*"))) + 1
                ten = f"{'_'.join(ds_the)}_{so:02d}{Path(f.name).suffix.lower()}"
                (thu_muc / ten).write_bytes(f.getvalue())
                st.success(f"Đã lưu {may}/{ten}")
