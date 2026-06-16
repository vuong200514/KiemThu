import os
import google.generativeai as genai
from dotenv import load_dotenv

# Tải các biến bí mật từ file .env lên
load_dotenv()

# Lấy chìa khóa
API_KEY = os.getenv("GEMINI_API_KEY")

def generate_test_cases(file_path):
    if not API_KEY:
        return {"status": "error", "message": "Chưa cài đặt GEMINI_API_KEY trong file .env"}
    
    # Đọc nội dung file gốc
    with open(file_path, 'r', encoding='utf-8') as file:
        source_code = file.read()

    try:
        # Khởi động AI
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Viết Prompt (Câu lệnh) ép AI làm QA Engineer
        prompt = f"""
        Đóng vai trò là một kỹ sư kiểm thử phần mềm (QA Engineer) giỏi Python.
        Hãy viết các unit test (sử dụng thư viện unittest) để kiểm tra đoạn source code sau.
        Bao phủ cả các trường hợp cơ bản và edge cases (trường hợp dị biệt).
        
        CHÚ Ý QUAN TRỌNG: 
        1. Chỉ trả về duy nhất mã nguồn Python, tuyệt đối không giải thích gì thêm.
        2. Không sử dụng markdown (như ```python ... ```).
        3. Trong code test, hãy import các hàm từ file gốc bằng cách giả định file gốc tên là '{os.path.basename(file_path).replace('.py', '')}'.
        
        Source code:
        {source_code}
        """
        
        # Gửi prompt cho AI và lấy kết quả
        response = model.generate_content(prompt)
        
        # Làm sạch kết quả (phòng hờ AI vẫn lén chèn markdown)
        cleaned_code = response.text.replace("```python", "").replace("```", "").strip()
        
        return {
            "status": "success",
            "test_code": cleaned_code
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}