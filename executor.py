import subprocess

def run_test_file(test_file_path):
    """Kích hoạt pytest để chạy file test và bắt kết quả"""
    try:

        result = subprocess.run(
            ["pytest", test_file_path, "-v"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            status = "passed"
        elif result.returncode == 1:
            status = "failed"
        else:
            status = "error"
            
        return {
            "status": status,
            "output": result.stdout,
            "error_log": result.stderr
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}