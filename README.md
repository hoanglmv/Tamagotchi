# ✨ myDeskAssistant - Frieren Anime Desktop Pet & AI MCP Assistant

Trợ lý ảo dạng **Desktop Pet** mang phong cách Anime **Sousou no Frieren** (Frieren: Pháp sư tiễn táng) nổi trên màn hình, được trang bị trí tuệ nhân tạo **Gemini 2.5 Flash** (qua OpenRouter) và hệ sinh thái công cụ cục bộ **FastMCP**.

---

## 🌸 Các nhân vật đồng hành (Frieren Characters)

Bạn có thể dễ dàng chuyển đổi qua lại giữa 4 nhân vật bằng cách **click chuột phải** lên nhân vật hoặc gõ lệnh trong CLI:

1. **Frieren (Pháp sư Ngàn năm)**: Điềm tĩnh, ngái ngủ, đam mê sưu tầm ma pháp kỳ quặc, hoài niệm về Himmel, so sánh phần cứng máy tính như dòng chảy Mana.
2. **Fern (Pháp sư Tập sự)**: Chu đáo, ngăn nắp, nghiêm túc, thỉnh thoảng phồng má giận dỗi `(´・ω・｀)` nhắc bạn đừng thức khuya hay lười biếng.
3. **Stark (Chiến binh dũng cảm)**: Trẻ trung, nhiệt huyết, hơi nhát gan trước lỗi hệ thống nhưng luôn sẵn sàng vung rìu gánh vác việc nặng, mê ăn Jumbo Parfait.
4. **Himmel (Dũng sĩ huyền thoại)**: Hào hoa, tự tin, yêu hoa và luôn khích lệ bạn tiến bước với nụ cười tỏa sáng.

---

## 🌟 Tính năng nổi bật

- **Cửa sổ nổi ghim màn hình (PyQt6)**: Trong suốt hoàn toàn, không viền, luôn nổi trên cùng, kéo thả chuột mượt mà.
- **Bóng thoại Glassmorphism**: Thiết kế kính mờ sang trọng hiển thị câu trả lời và ô nhập tin nhắn trực tiếp.
- **Biểu cảm & Hoạt ảnh động**: 3 trạng thái `idle` (thở nhẹ bồng bềnh), `thinking` (đang suy luận / chạy tool), và `talking` (khẩu hình cử động theo âm thanh).
- **Hệ thống công cụ MCP (Model Context Protocol)**:
  - `get_pc_stats`: Kiểm tra % CPU, RAM trống, ổ cứng, dung lượng pin.
  - `launch_app`: Khởi chạy ứng dụng máy tính (Chrome, VS Code, Notepad, Calculator...).
  - `organize_downloads`: Quét và tự động phân loại file tải về theo danh mục (Images, Documents, Installers...).
  - `read_file` / `write_file` / `list_directory`: Thao tác dữ liệu cục bộ.
- **Giọng nói Anime (Edge-TTS)**: Phát âm thanh tiếng Việt tự nhiên (`vi-VN-HoaiMyNeural` hoặc `vi-VN-NamMinhNeural`).
- **Ký ức hội thoại (SQLite)**: Lưu trữ lịch sử tin nhắn và ngữ cảnh nhiều lượt tại `data/memory.db`.
- **Đóng gói đa nền tảng**: Hỗ trợ xuất file chạy độc lập cho cả **Windows (.exe)** và **Linux** thông qua GitHub Actions Release.

---

## 🚀 Hướng dẫn cài đặt & Chạy ứng dụng

### 1. Cài đặt môi trường
```bash
# Tạo môi trường ảo Python 3.12
python3 -m venv .venv

# Kích hoạt môi trường ảo:
# Trên Linux/macOS:
source .venv/bin/activate
# Trên Windows:
# .venv\Scripts\activate

# Cài đặt thư viện:
pip install -r requirements.txt
```

### 2. Cấu hình file `.env`
Mở file `.env` và điền khóa API của bạn:
```env
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxx
OPENROUTER_MODEL=google/gemini-2.5-flash
TTS_VOICE=vi-VN-HoaiMyNeural
```

### 3. Chạy ứng dụng
- **Chế độ Desktop Pet GUI (Giao diện nổi)**:
  ```bash
  python main.py
  ```
- **Chế độ dòng lệnh Terminal (CLI)**:
  ```bash
  python main.py --cli
  ```

---

## 📦 Đóng gói & Phát hành Release trên GitHub

### Cách 1: Tự động qua GitHub Actions (Khuyên dùng)
Khi bạn push một git tag phiên bản lên GitHub, quy trình CI/CD sẽ tự động biên dịch trên Windows & Linux và tạo bản Release:
```bash
git add .
git commit -m "feat: complete myDeskAssistant Frieren release setup"
git tag v1.0.0
git push origin main --tags
```
Sau đó vào tab **Releases** trên kho lưu trữ GitHub của bạn để tải về:
- `myDeskAssistant-windows-x64.zip`
- `myDeskAssistant-linux-x64.tar.gz`

### Cách 2: Đóng gói cục bộ bằng PyInstaller
Chạy lệnh trực tiếp trên máy của bạn:
```bash
python build.py
```
Ứng dụng hoàn chỉnh sẽ được tạo ra tại thư mục `dist/myDeskAssistant`.
