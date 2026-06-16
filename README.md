# AutoTestTool

Giới thiệu ngắn
----------------
AutoTestTool là một bộ công cụ nhỏ giúp tự động sinh và chạy unit test cho file mã nguồn Python. Quy trình chính:
- Phân tích tĩnh file nguồn (đếm hàm/lớp).
- Gọi Ollama local để sinh mã test (định dạng `unittest`).
- Lưu file test do AI sinh và chạy bằng `pytest`.

Cấu trúc chính
--------------
- `ai_generator.py`: Gọi Ollama để sinh test case từ source code. Model mặc định là `qwen2.5-coder:7b`, có thể đổi bằng biến môi trường `OLLAMA_MODEL`.
- `analyzer.py`: Phân tích tĩnh file Python bằng `ast`, trả về số hàm và lớp và bắt lỗi cú pháp.
- `executor.py`: Chạy file test bằng `pytest` và trả về output cùng trạng thái (passed/failed/error).
- `main.py`: CLI điều phối toàn bộ pipeline — nhận file nguồn, phân tích, gọi AI, tạo file test, chạy test và in kết quả bằng `rich`.
- `project_analysis.md`: Ghi chú phân tích/ý tưởng (không bắt buộc cho pipeline chính).
- `sample.py`: File ví dụ chứa vài hàm mẫu (`sum`, `multiply`, `Calculator`).
- `test_sample.py`: Bộ test mẫu (sử dụng `unittest`) cho `sample.py`.

Yêu cầu & Cài đặt nhanh
----------------------
1. Tạo virtual environment (Windows):

```
python -m venv venv
.
venv\Scripts\Activate.ps1   # PowerShell
venv\Scripts\activate.bat   # CMD
```

2. Cài phụ thuộc (gợi ý):

```
pip install -U pip
pip install google-generativeai python-dotenv rich pytest
```

Gợi ý thêm (nếu muốn): tạo `requirements.txt`:

```
google-generativeai
python-dotenv
rich
pytest
```

Lưu ý: Cần chạy `ollama serve` và tải model bằng `ollama pull qwen2.5-coder:7b`.

Cấu hình `.env`
----------------
Tạo file `.env` ở thư mục gốc với dòng:

```
OLLAMA_MODEL=qwen2.5-coder:7b
OLLAMA_API_URL=http://localhost:11434/api/generate
```

Cách dùng
---------
- Chạy toàn bộ pipeline cho file `sample.py`:

```
python main.py sample.py
```

- Chạy bộ test mẫu bằng pytest:

```
pytest -q
```

Hoạt động chi tiết theo file
---------------------------
- `ai_generator.py`:
  - Hàm chính: `generate_test_cases(file_path)`
  - Đọc file, dựng prompt cho Ollama, yêu cầu AI trả về mã `unittest` thuần túy.
  - Trả về dict với `status` và `test_code` hoặc `message` khi có lỗi.

- `analyzer.py`:
  - Hàm: `analyze_python_file(file_path)`
  - Dùng `ast.parse` rồi đếm `FunctionDef` và `ClassDef`.
  - Trả về `syntax_error` nếu mã có lỗi cú pháp để tránh gọi AI trên mã hỏng.

- `executor.py`:
  - Hàm: `run_test_file(test_file_path)`
  - Gọi `pytest <file> -v` qua `subprocess.run`, bắt stdout/stderr và `returncode`.
  - Chuẩn hoá thành `status` = `passed`/`failed`/`error`.

- `main.py`:
  - Giao diện CLI (argparse) và hiển thị đẹp bằng `rich`.
  - Quy trình:
    1. Kiểm tra file tồn tại.
    2. Gọi `analyze_python_file`.
    3. Nếu OK, gọi `generate_test_cases` (AI).
    4. Ghi file `test_<original>.py` và gọi `run_test_file`.
    5. In kết quả chi tiết.

Ví dụ nhanh
-----------
1. Kiểm tra file mẫu:

```
python main.py sample.py
```

2. Nếu bạn muốn chạy `test_sample.py` (test viết tay):

```
pytest test_sample.py -q
```

Gợi ý cải tiến (Next steps)
---------------------------
- Thêm `requirements.txt` và file `install.sh` / `install.ps1` để tự động hoá cài đặt.
- Kiểm tra kỹ prompt trong `ai_generator.py` để hạn chế AI sinh code có lỗi cú pháp.
- Thêm kiểm tra an toàn trước khi chạy test sinh tự động (ví dụ sandboxing).
- Xử lý các trường hợp AI trả về code có encoding khác hoặc kèm chú thích không mong muốn.

Nếu bạn muốn, tôi có thể:
- Tạo `requirements.txt` từ imports hiện tại.
- Tạo file `.env.example` và cập nhật `README.md` với ví dụ cấu hình.
- Viết hướng dẫn chạy CI (GitHub Actions) để tự động chạy `pytest`.
