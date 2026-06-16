import os 
import shutil 

from fastapi import FastAPI ,UploadFile ,File ,HTTPException 

from fastapi .responses import HTMLResponse 

from fastapi .staticfiles import StaticFiles 

from fastapi .middleware .cors import CORSMiddleware 


from analyzer import analyze_python_file 
from ai_generator import generate_test_cases 
from executor import run_test_file 
from reporter import generate_report 

from pydantic import BaseModel 
from typing import List ,Optional 



# Tóm tắt: Không có docstring cho ReportInfo
class ReportInfo (BaseModel ):
    file_name :str 
    status :str 
    report_url :Optional [str ]=None 
    message :Optional [str ]=None 

app =FastAPI (title ="AutoTestTool API")


app .add_middleware (
CORSMiddleware ,
allow_origins =["*"],
allow_credentials =True ,
allow_methods =["*"],
allow_headers =["*"],
)


app .mount ("/frontend",StaticFiles (directory ="frontend",html =True ),name ="frontend")

if not os .path .exists ("reports"):
    os .makedirs ("reports")
app .mount ("/reports",StaticFiles (directory ="reports"),name ="reports")



# Tóm tắt: đọc
@app .get ("/",response_class =HTMLResponse )
async def read_index ():
    with open ("frontend/index.html","r",encoding ="utf-8")as f :
        return f .read ()



# Tóm tắt: API endpoint nhận file và chạy luồng kiểm thử như main. py
@app .post ("/api/test-file")
async def test_file_api (file :UploadFile =File (...)):
    """API endpoint nhận file và chạy luồng kiểm thử như main.py"""
    if not file .filename .endswith (".py"):
        return {"status":"error","message":"Chỉ hỗ trợ file Python (.py)"}


    file_path =f"uploaded_{file.filename}"
    with open (file_path ,"wb")as buffer :
        shutil .copyfileobj (file .file ,buffer )

    try :

        analyze_result =analyze_python_file (file_path )
        if analyze_result ["status"]!="success":
            return {"status":"error","message":analyze_result ["message"],"analyze_result":analyze_result }


        ai_result =generate_test_cases (file_path )
        if ai_result ["status"]!="success":
            return {"status":"error","message":ai_result ["message"],"analyze_result":analyze_result }


        test_file_name =f"test_{file.filename}"
        with open (test_file_name ,"w",encoding ="utf-8")as f :
            f .write (ai_result ["test_code"])


        exec_result =run_test_file (test_file_name )


        try :
            html_path =generate_report (file_path ,test_file_name ,exec_result .get ('output',''))

            report_url =f"/{html_path}"
        except Exception as e :
            report_url =None 
            print ("Lỗi khi tạo báo cáo:",e )

        return {
        "status":"success",
        "analyze_result":analyze_result ,
        "ai_result":ai_result ,
        "exec_result":exec_result ,
        "report_url":report_url 
        }

    except Exception as e :
        return {"status":"error","message":str (e )}


if __name__ =="__main__":

    import uvicorn 
    uvicorn .run ("api:app",host ="127.0.0.1",port =8000 ,reload =True )
