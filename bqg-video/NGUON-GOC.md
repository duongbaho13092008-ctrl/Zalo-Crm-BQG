# Nguồn gốc và giấy phép — Xưởng Video A.I Bình Quân

## Ý tưởng tham khảo

Thiết kế dây chuyền 6 khâu (kịch bản → từ khoá → giọng đọc → phụ đề → cảnh quay → dựng) tham khảo
**[harry0703/MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo)**, giấy phép **MIT**,
đọc mã tại commit `53c4ca3` (10/11/2026).

**Mã nguồn Python trong thư mục này được viết lại mới hoàn toàn**, không chép mã từ MoneyPrinterTurbo.
Điểm khác về thiết kế xem bảng "Khác gì bản gốc" trong `README.md`.

Ghi công theo tinh thần giấy phép MIT của bản gốc:

```
MIT License

Copyright (c) 2024 Harry

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Tài nguyên bên thứ ba kèm theo

| Tài nguyên | Nguồn | Giấy phép |
|---|---|---|
| Font Be Vietnam Pro (`resource/fonts/BeVietnamPro-*.ttf`) | The Be Vietnam Pro Project Authors | SIL Open Font License 1.1 — `resource/fonts/OFL-BeVietnamPro.txt` |
| Logo Bình Quân (`resource/logo-bqg.png`) | Bình Quân Group (cắt tròn từ `frontend/public/brand/bqg-logo-square.png`) | Tài sản thương hiệu BQG |

## Thư viện dùng khi chạy (cài qua `requirements.txt`)

ffmpeg (LGPL/GPL, cài riêng), edge-tts (LGPL-3.0), anthropic (MIT), fastapi (MIT), uvicorn (BSD), streamlit (Apache-2.0),
pydantic (MIT), pillow (MIT-CMU), numpy (BSD), loguru (MIT), requests (Apache-2.0), imageio-ffmpeg (BSD).

## Giấy phép phần BQG viết

Theo giấy phép của kho này (Apache License 2.0, tệp `LICENSE` ở thư mục gốc).
