import subprocess 
import sys 



# Tóm tắt: Kích hoạt pytest để chạy file test và bắt kết quả
def run_test_file (test_file_path ):
    """Kích hoạt pytest để chạy file test và bắt kết quả"""
    try :

        result =subprocess .run (
        [sys .executable ,"-m","pytest",test_file_path ,"-v"],
        capture_output =True ,
        text =True 
        )


        if result .returncode ==0 :
            status ="passed"
        elif result .returncode ==1 :
            status ="failed"
        else :
            status ="error"


        output =result .stdout 
        if not output and result .stderr :
            output =result .stderr 

        return {
        "status":status ,
        "output":output ,
        "error_log":result .stderr 
        }

    except Exception as e :

        error_str =f"Lỗi thực thi: {str(e)}"
        return {"status":"error","message":error_str ,"output":error_str }
