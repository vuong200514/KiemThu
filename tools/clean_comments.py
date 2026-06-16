import ast 
import io 
import os 
import re 
import sys 
import tokenize 


EMOJI_PATTERN =re .compile (
"["
"\U0001F300-\U0001F5FF"
"\U0001F600-\U0001F64F"
"\U0001F680-\U0001F6FF"
"\U0001F700-\U0001F77F"
"\U0001F780-\U0001F7FF"
"\U0001F800-\U0001F8FF"
"\U0001F900-\U0001F9FF"
"\U0001FA00-\U0001FA6F"
"\U00002702-\U000027B0"
"\U000024C2-\U0001F251"
"]+",
flags =re .UNICODE ,
)




# Tóm tắt: Remove all COMMENT tokens while preserving code and string contents.
def remove_comments_from_python (source :str )->str :
    """Remove all COMMENT tokens while preserving code and string contents."""
    sio =io .StringIO (source )
    tokens =[]
    try :
        for tok in tokenize .generate_tokens (sio .readline ):
            tok_type =tok .type 
            tok_string =tok .string 
            if tok_type ==tokenize .COMMENT :
                continue 
            tokens .append ((tok_type ,tok_string ))
        return tokenize .untokenize (tokens )
    except Exception :
        return source 




# Tóm tắt: Không có docstring cho strip_emojis
def strip_emojis (text :str )->str :
    return EMOJI_PATTERN .sub ("",text )


# Tóm tắt: Simple rule - based English - > Vietnamese translator for short summaries.
def translate_en_to_vi (text :str )->str :
    """Simple rule-based English->Vietnamese translator for short summaries."""
    if not text :
        return text 

    phrase_map ={
    "a mock storage class to simulate tinydb's storage behavior.":
    "Lớp lưu trữ giả để mô phỏng hành vi lưu trữ của TinyDB.",
    "a mock table class to simulate tinydb's table behavior.":
    "Lớp bảng giả để mô phỏng hành vi bảng của TinyDB.",
    "a mock table class to simulate table behavior.":
    "Lớp bảng giả để mô phỏng hành vi bảng.",
    "a mock storage class to simulate storage behavior.":
    "Lớp lưu trữ giả để mô phỏng hành vi lưu trữ.",
    "no docstring for":"Không có docstring cho",
    "to simulate":"để mô phỏng",
    "mock":"giả (mock)",
    "storage":"lưu trữ",
    "class":"lớp",
    "table":"bảng",
    "read":"đọc",
    "write":"ghi",
    "close":"đóng",
    "behavior":"hành vi",
    }

    s =text .strip ()
    lower =s .lower ()
    for k ,v in phrase_map .items ():
        if k in lower :
            return v 

    tokens =re .findall (r"\w+|[^\w\s]",s ,re .UNICODE )
    out_tokens =[]
    for t in tokens :
        tl =t .lower ()
        if tl in phrase_map :
            out_tokens .append (phrase_map [tl ])
        else :
            out_tokens .append (t )
    return " ".join (out_tokens ).replace (" ,",",").replace (" .",".")




# Tóm tắt: lớp
def insert_short_comments (source :str )->str :
    """Insert one short comment above each function or class definition describing its purpose.

    Uses the first line of the existing docstring when available, otherwise a generic short note.
    """
    try :
        tree =ast .parse (source )
    except Exception :
        return source 


    inserts =[]
    for node in ast .walk (tree ):
        if isinstance (node ,(ast .FunctionDef ,ast .AsyncFunctionDef ,ast .ClassDef )):
            doc =ast .get_docstring (node )
            if doc :
                short =doc .strip ().splitlines ()[0 ]
            else :
                short =f"Không có docstring cho {node.name}"
            short_vi =translate_en_to_vi (short )
            comment =f"# Tóm tắt: {short_vi}\n"
            inserts .append ((node .lineno ,comment ))

    if not inserts :
        return source 


    lines =source .splitlines (keepends =True )
    for lineno ,comment in sorted (inserts ,reverse =True ):
        idx =lineno -1 

        while idx >0 and lines [idx -1 ].lstrip ().startswith ("@"):
            idx -=1 
        lines .insert (idx ,comment )

    return "".join (lines )




# Tóm tắt: Không có docstring cho process_file
def process_file (path :str )->bool :
    try :
        with open (path ,"r",encoding ="utf-8")as f :
            src =f .read ()
    except Exception :
        return False 

    orig =src 
    src =strip_emojis (src )
    src =remove_comments_from_python (src )
    src =insert_short_comments (src )

    if src !=orig :
        with open (path ,"w",encoding ="utf-8")as f :
            f .write (src )
        return True 
    return False 




# Tóm tắt: Không có docstring cho find_py_files
def find_py_files (root :str ):
    for dirpath ,dirnames ,filenames in os .walk (root ):

        if "venv"in dirpath .split (os .sep )or ".venv"in dirpath .split (os .sep ):
            continue 
        for fn in filenames :
            if fn .endswith (".py"):
                yield os .path .join (dirpath ,fn )




# Tóm tắt: Không có docstring cho main
def main ():
    root =os .getcwd ()
    changed =[]
    for path in find_py_files (root ):
        ok =process_file (path )
        if ok :
            changed .append (path )

    print ("Files modified:")
    for p in changed :
        print (p )


if __name__ =="__main__":
    main ()
