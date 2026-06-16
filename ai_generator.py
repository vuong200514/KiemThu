import os 

import google .generativeai as genai 

from dotenv import load_dotenv 


load_dotenv ()


API_KEY =os .getenv ("GEMINI_API_KEY")



# Tóm tắt: Gửi code cho AI để nó tự động viết Unit Test
def generate_test_cases (file_path ):
    """Gửi code cho AI để nó tự động viết Unit Test"""
    if not API_KEY :
        return {"status":"error","message":"Chưa cài đặt GEMINI_API_KEY trong file .env"}


    with open (file_path ,'r',encoding ='utf-8')as file :
        source_code =file .read ()

    try :

        genai .configure (api_key =API_KEY )
        model =genai .GenerativeModel ('gemini-2.5-flash')


        prompt =f"""
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


        import time 
        max_retries =3 
        response =None 

        for attempt in range (max_retries ):
            try :
                response =model .generate_content (prompt )
                break 
            except Exception as e :
                error_str =str (e ).lower ()
                if "429"in error_str or "quota"in error_str or "exhausted"in error_str :
                    if attempt <max_retries -1 :
                        print (f"Bị giới hạn API (Quota). Đang chờ 35 giây để thử lại... (Lần {attempt + 1}/{max_retries})")
                        time .sleep (35 )
                        continue 
                raise e 

        if not response :
            raise Exception ("Không thể kết nối với AI sau nhiều lần thử.")


        cleaned_code =response .text .replace ("```python","").replace ("```","").strip ()

        return {
        "status":"success",
        "test_code":cleaned_code 
        }
    except Exception as e :
        return {"status":"error","message":str (e )}