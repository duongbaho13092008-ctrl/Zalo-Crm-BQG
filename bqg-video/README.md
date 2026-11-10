# Xưởng Video A.I Bình Quân

Dây chuyền dựng video ngắn (TikTok, Reels, YouTube Shorts) **từ cảnh máy chạy thật** của Bình Quân Group.
Viết lại hoàn toàn cho BQG, lấy ý tưởng dây chuyền 6 khâu của MoneyPrinterTurbo (xem `NGUON-GOC.md`).

> Đây là **dây chuyền dựng video**, không phải "máy in tiền". Video tốt vẫn phải bắt đầu từ lời khách thật,
> cảnh máy chạy thật và con số đã xác minh. Phần mềm chỉ giúp dựng nhanh những thứ đó.

> 📘 **Hướng dẫn chi tiết có ảnh chụp giao diện thật:** mở `docs/HUONG-DAN-SU-DUNG.html` bằng trình duyệt.

## Dây chuyền 6 khâu

| Khâu | Làm gì | Ai chịu |
|---|---|---|
| 1. Kịch bản | Từ lời khách thật (đã ẩn danh) → A.I viết hoặc tự viết. Mỗi chủ đề nhiều **biến thể chỉ khác câu mở đầu** | Marketing, Sales duyệt |
| 2. Thẻ cảnh | Mỗi đoạn lời đọc gắn thẻ cảnh (`may-chay`, `vien-cam`...) lấy đúng từ kho | Phần mềm |
| 3. Giọng đọc | Giọng máy Hoài My (nữ) / Nam Minh (nam), hoặc **tệp ghi âm người thật** (giọng miền) | Marketing |
| 4. Phụ đề | Chữ to Be Vietnam Pro, viền đen, nền mờ — đọc được khi tắt tiếng | Phần mềm |
| 5. Cảnh thật | Khớp cảnh theo thứ tự kịch bản, **chỉ lấy cảnh đúng dòng máy** + cảnh chung | Phần mềm |
| 6. Dựng & duyệt | Logo, mã video, cảnh kết có lời kêu gọi → **CHỜ DUYỆT**. Không có tự đăng | Trưởng Marketing |

## Khác gì bản gốc MoneyPrinterTurbo

| Bản gốc | Bản BQG |
|---|---|
| Lấy cảnh kho miễn phí (Pexels, Pixabay), tìm bằng từ khoá tiếng Anh | **Chỉ kho cảnh thật của BQG**, chia theo dòng máy, không bao giờ lấy cảnh máy khác dòng |
| A.I viết kịch bản chung chung | Chỉ dẫn gốc giọng nhà nông, **cấm bịa số**, cấm cường điệu, không báo giá, không hứa ngày giao |
| Không kiểm nội dung | **Bộ kiểm kịch bản**: chặn "tốt nhất / số 1 / cam kết 100% / hoàn vốn ngay", đánh dấu số liệu không có trong bằng chứng, chặn SĐT/email khách |
| Gửi nguyên văn cho A.I | **Ẩn danh SĐT, email, số tài khoản** trước khi gửi A.I; có thể chạy A.I ngay trên máy (Ollama) |
| Tự đăng lên mạng xã hội | **Bỏ tự đăng.** Duyệt 6 mục kiểm, ghi tên người duyệt, rồi mới ghi nhận đăng |
| Đo bằng lượt xem | **Mã video** in trên video + cảnh kết → đếm **lead đủ 4 câu lọc** và **đơn máy thực** theo từng video |
| API mở `0.0.0.0`, không khoá | API chỉ nghe `127.0.0.1`; mở ra mạng mà không đặt khoá thì **từ chối khởi động** |
| ~40.000 dòng, 14 nguồn cảnh, 12 dịch vụ giọng | ~2.800 dòng (cả giao diện), đủ dùng, dễ sửa |

## Cài đặt (máy văn phòng, không cần card đồ hoạ)

Cần: **Python 3.11+** và **ffmpeg** (công cụ xử lý video). Windows chưa có ffmpeg thì gói `imageio-ffmpeg` tự mang theo.

```bash
cd bqg-video
cp config.example.toml config.toml        # sửa hotline, Zalo trong [thuong_hieu]
python -m venv .venv
.venv/bin/pip install -r requirements.txt   # Windows: .venv\Scripts\pip install -r requirements.txt
export ANTHROPIC_API_KEY=...                # khoá Claude để A.I viết kịch bản (không có thì vẫn dán kịch bản tay được)
.venv/bin/streamlit run webui/app.py        # mở http://127.0.0.1:8501
```

Hoặc bấm đúp `chay-giao-dien.bat` (Windows) / chạy `./chay-giao-dien.sh` (Linux, macOS) — tự cài lần đầu.

Docker (đóng gói chạy sẵn): `cp config.example.toml config.toml && docker compose up -d giao-dien`.

**Mạng:** giọng máy Edge TTS (dịch vụ đọc chữ thành giọng của Microsoft, miễn phí, không cần khoá) cần Internet.
Không có mạng → dùng tệp ghi âm hoặc chế độ không giọng.

## Cách dùng — 5 bước trong phễu D2C

1. **Kho cảnh thật** (Marketing + Kỹ thuật): quay 30–50 đoạn 5–10 giây — máy chạy, viên cám ra, khách cầm viên cám,
   nhà xưởng. Tải lên ở thẻ *Kho cảnh thật* hoặc chép vào `kho-canh/` theo hướng dẫn `kho-canh/README.md`.
2. **Kịch bản từ lời khách** (Marketing, Sales duyệt): dán câu hỏi / nỗi đau thật từ Zalo, cuộc gọi; điền
   **bằng chứng đã xác minh** (chỉ những số được phép nói). A.I viết 3 biến thể câu mở đầu; sửa tay thoải mái.
3. **Dựng nhiều biến thể** (Marketing): mỗi chủ đề 3 biến thể, mỗi lần chỉ đổi **một** yếu tố — câu mở đầu.
4. **Duyệt rồi mới đăng** (Trưởng Marketing): tích đủ 6 mục kiểm — số liệu đúng, không hứa quá, đúng máy,
   không lộ khách, nhạc hợp lệ, mã video hiện rõ. Kịch bản còn lỗi CHẶN thì không duyệt được.
5. **Đo tới đơn** (Marketing + Sales): Sales ghi **mã video** vào trường nguồn của khách trên CRM; cập nhật số
   lead đủ 4 câu lọc và đơn máy thực ở thẻ *Đăng & đo lead* (hoặc CRM đẩy qua API). Giữ công thức của nhóm video tốt nhất.

## Mã video — sợi chỉ nối video với đơn máy

`V-EPCAM-261110-01B` = **V**ideo · máy **ép cám** · ngày **10/11/2026** · chủ đề số **01** · biến thể **B**.

- Mã in nhỏ góc trên phải suốt video (giữ nguồn khi video bị đăng lại) và **to ở cảnh kết**: "Nhắn mã: V-...".
- Khách nhắn mã qua Zalo → tổng đài/Sales ghi đúng nguồn.
- Link website gắn mã bằng UTM (tham số đo nguồn truy cập): `python -m bqgvideo utm <link> <mã> TikTok`.
- Ô số đo để trống = **Chưa có dữ liệu**, không phải 0. Ngưỡng giữ / bỏ biến thể do Sếp chốt, phần mềm không tự kết luận.

**Bộ lọc 4 câu** (lead đủ 4 câu = SQL — lead đủ tiêu chuẩn Sales): nuôi gì, quy mô bao nhiêu · tự trộn hay mua cám
ngoài · ai quyết mua · định làm trong bao lâu. Câu kêu gọi mặc định đã mời khách nói luôn 2 câu đầu.

## Dòng lệnh (CLI — gõ lệnh, không cần giao diện)

```bash
python -m bqgvideo kho-canh                                   # xem kho cảnh theo dòng máy
python -m bqgvideo kich-ban --chu-de "Cám nổi cho ao cá" --dong-may may-ep-cam-vien \
    --loi-khach "Nuôi 3 ao trắm, tiền cám hơn chục triệu/tháng" --bang-chung "300 kg/giờ tại trại khách cũ" \
    --ra kb.json
python -m bqgvideo kiem-tra --kich-ban kb.json
python -m bqgvideo dung --kich-ban kb.json --giong vi-VN-HoaiMyNeural --nhac nhac-cua-bqg.mp3
python -m bqgvideo duyet V-EPCAM-261110-01A --nguoi "Tên trưởng MKT" --da-kiem-het
python -m bqgvideo dang V-EPCAM-261110-01A --kenh TikTok --lien-ket https://...
python -m bqgvideo do-luong V-EPCAM-261110-01A --lead-du-4-cau 4 --don-may-thuc 1 --nguon-so "CRM BQG"
python -m bqgvideo so-do --csv so-do.csv                      # mở bằng Excel
```

Kịch bản tự viết (`.txt`): dòng `MO:` là câu mở đầu (mỗi dòng 1 biến thể), dòng cuối là câu kêu gọi,
thẻ cảnh ghi cuối dòng trong ngoặc vuông: `Viên ra đều tay [vien-cam, khuon]`.

## API cho CRM BQG (cổng kết nối phần mềm)

`python -m bqgvideo api` → `http://127.0.0.1:8686`, tài liệu tự sinh tại `/docs`. Có khoá thì gửi header `X-API-Key`.

| Lệnh | Việc |
|---|---|
| `POST /api/v1/kich-ban` | A.I viết kịch bản + cảnh báo theo biến thể |
| `POST /api/v1/kiem-tra` | Kiểm một lời đọc |
| `POST /api/v1/tai-len` | Tải tệp ghi âm, trả `ten_tep` |
| `POST /api/v1/videos` | Dựng (chạy nền), trả `ma_viec`; xem tiến độ ở `GET /api/v1/viec/{ma_viec}` |
| `GET /api/v1/videos`, `/videos/{ma}`, `/videos/{ma}/tep/video.mp4` | Danh sách, chi tiết, tải video |
| `POST /api/v1/videos/{ma}/duyet`, `/dang` | Duyệt, ghi nhận đăng |
| `PATCH /api/v1/videos/{ma}/do-luong` | **CRM đẩy số lead đủ 4 câu / đơn máy thực theo mã video** |
| `GET /api/v1/tong-hop`, `/so-do.csv` | So biến thể theo chủ đề, xuất sổ đo |

## An toàn dữ liệu

- Khoá A.I và khoá API chỉ đặt bằng **biến môi trường**, không ghi vào tệp cấu hình.
- Lời khách được ẩn SĐT, email, số tài khoản, link Zalo/Facebook cá nhân **trước khi gửi A.I**. Tên người không lọc
  tự động được — người duyệt kiểm ở mục "Không lộ khách".
- Muốn không gửi gì ra ngoài: `[llm] provider = "ollama"` (A.I chạy ngay trên máy BQG).
- A.I Claude bật **dự phòng phía máy chủ** (server-side fallback): nếu mô hình chính từ chối một yêu cầu, API tự chạy lại
  trên mô hình dự phòng. Tắt bằng cách bỏ tham số `fallbacks` trong `bqgvideo/ai_viet.py`.
- Chỉ tải gói từ thư mục này. Gói tên `MoneyPrinterTurbo` trên PyPI (kho gói Python) là của bên thứ ba.

## Giới hạn hiện tại

- Giọng máy chỉ có 2 giọng chuẩn Bắc; giọng miền → thu âm người thật rồi tải lên.
- Tệp ghi âm chỉ khớp **một** biến thể (vì câu mở đầu khác nhau).
- Chưa nối tự động vào CRM BQG: API đã sẵn sàng, cần đội phần mềm gọi `PATCH .../do-luong`.
- **Chưa có dữ liệu** về hiệu quả của công cụ với khách BQG — đề xuất thử 2 tuần: 10 chủ đề × 3 biến thể, so lead đủ
  4 câu lọc với video đang làm tay; ngưỡng giữ / bỏ do Sếp đặt.

## Kiểm thử

```bash
pip install -r requirements-dev.txt
python -m pytest           # 52 bài, gồm dựng video thật bằng ffmpeg với cảnh giả lập
```

---
Bình Quân Group — Đồng hành cùng nhà nông từ 1990.
