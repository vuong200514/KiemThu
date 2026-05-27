import ast

def analyze_python_file(file_path):
    """Đọc và phân tích cấu trúc file Python."""
    # Đọc nội dung file
    with open(file_path, 'r', encoding='utf-8') as file:
        source_code = file.read()

    try:
        # Cố gắng dịch code thành 'Cây cú pháp' (AST)
        tree = ast.parse(source_code)
        
        # Tìm và đếm số lượng Hàm và Class
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        
        return {
            "status": "success",
            "functions_count": len(functions),
            "classes_count": len(classes)
        }
        
    except SyntaxError as e:
        # Nếu code bị sai cú pháp, bắt lỗi và báo lại
        error_line = e.text.strip() if e.text else "Không rõ"
        return {
            "status": "syntax_error",
            "message": f"Lỗi ở dòng {e.lineno}: {error_line}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }