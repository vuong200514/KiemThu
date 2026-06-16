import ast
import os


import ast
import os
import glob

def _cyclomatic_complexity(func_node) -> int:
    count = 1
    for node in ast.walk(func_node):
        if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                              ast.With, ast.Assert, ast.comprehension)):
            count += 1
        elif isinstance(node, ast.BoolOp):
            count += len(node.values) - 1
    return count

def scan_directory(dir_path):
    if not os.path.isdir(dir_path):
        return {"status": "error", "message": "Thư mục không tồn tại"}

    nodes = []
    edges = []
    file_count = 0
    func_count = 0

    dir_id = "dir_root"
    nodes.append({
        "id": dir_id,
        "label": os.path.basename(dir_path) or dir_path,
        "type": "directory"
    })

    py_files = glob.glob(os.path.join(dir_path, "**/*.py"), recursive=True)
    # Ignore some directories to avoid clutter
    py_files = [f for f in py_files if ".venv" not in f and "venv" not in f and "__pycache__" not in f and ".git" not in f]

    for file_path in py_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source)
            
            rel_path = os.path.relpath(file_path, dir_path)
            file_id = f"file_{rel_path}"
            
            functions = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            
            nodes.append({
                "id": file_id,
                "label": os.path.basename(file_path),
                "type": "file",
                "path": file_path,
                "func_count": len(functions)
            })
            edges.append({"from": dir_id, "to": file_id})
            
            file_count += 1
            func_count += len(functions)
            
            # Add top-level functions and classes to graph
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    fid = f"{file_id}_{node.name}"
                    ftype = "async_function" if isinstance(node, ast.AsyncFunctionDef) else "function"
                    nodes.append({
                        "id": fid,
                        "label": node.name,
                        "type": ftype,
                        "func_name": node.name,
                        "path": file_path,
                        "lineno": node.lineno,
                        "complexity": _cyclomatic_complexity(node)
                    })
                    edges.append({"from": file_id, "to": fid})
                elif isinstance(node, ast.ClassDef):
                    cid = f"{file_id}_{node.name}"
                    methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                    nodes.append({
                        "id": cid,
                        "label": node.name,
                        "type": "class",
                        "path": file_path,
                        "lineno": node.lineno,
                        "method_count": len(methods)
                    })
                    edges.append({"from": file_id, "to": cid})
                    for m in methods:
                        mid = f"{cid}_{m.name}"
                        mtype = "async_method" if isinstance(m, ast.AsyncFunctionDef) else "method"
                        nodes.append({
                            "id": mid,
                            "label": m.name,
                            "type": mtype,
                            "func_name": m.name,
                            "class_name": node.name,
                            "path": file_path,
                            "lineno": m.lineno,
                            "complexity": _cyclomatic_complexity(m)
                        })
                        edges.append({"from": cid, "to": mid})
        except Exception:
            pass

    return {
        "status": "success",
        "file_count": file_count,
        "func_count": func_count,
        "nodes": nodes,
        "edges": edges
    }

def _get_docstring(node):
    if (node.body and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)):
        return node.body[0].value.value.strip()
    return None


def _get_annotation(node):
    try:
        return ast.unparse(node)
    except Exception:
        return None


def _extract_raises(func_node):
    raises = []
    for node in ast.walk(func_node):
        if isinstance(node, ast.Raise) and node.exc is not None:
            try:
                raises.append(ast.unparse(node.exc))
            except Exception:
                pass
    return list(dict.fromkeys(raises))


def _extract_calls(func_node):
    calls = []
    for node in ast.walk(func_node):
        if isinstance(node, ast.Call):
            try:
                calls.append(ast.unparse(node.func))
            except Exception:
                pass
    return list(dict.fromkeys(calls))


def _extract_returns(func_node):
    returns = []
    has_value_return = False
    for node in ast.walk(func_node):
        if isinstance(node, ast.Return):
            if node.value is None:
                returns.append("None")
            else:
                has_value_return = True
                try:
                    returns.append(ast.unparse(node.value))
                except Exception:
                    returns.append("<value>")
    return list(dict.fromkeys(returns)), has_value_return


def _extract_function_info(node):
    args = []
    func_args = node.args
    all_args = func_args.args
    defaults = func_args.defaults
    default_offset = len(all_args) - len(defaults)

    for i, arg in enumerate(all_args):
        info = {"name": arg.arg}
        if arg.annotation:
            info["type"] = _get_annotation(arg.annotation)
        if i >= default_offset:
            try:
                info["default"] = ast.unparse(defaults[i - default_offset])
            except Exception:
                pass
        args.append(info)

    # *args, **kwargs
    if func_args.vararg:
        args.append({"name": f"*{func_args.vararg.arg}"})
    if func_args.kwarg:
        args.append({"name": f"**{func_args.kwarg.arg}"})

    returns, has_value_return = _extract_returns(node)

    return {
        "name": node.name,
        "args": args,
        "return_type": _get_annotation(node.returns) if node.returns else None,
        "docstring": _get_docstring(node),
        "raises": _extract_raises(node),
        "returns": returns,
        "has_value_return": has_value_return,
        "calls": _extract_calls(node),
        "lineno": node.lineno,
        "is_async": isinstance(node, ast.AsyncFunctionDef),
    }


def extract_ast_summary(file_path):
    """
    Trả về dict đầy đủ:
    - imports: list string
    - functions: list thông tin hàm top-level
    - classes: list class với methods
    - source_code: toàn bộ source
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        source_code = f.read()

    tree = ast.parse(source_code)

    # Imports
    imports = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(f"import {alias.name}" + (f" as {alias.asname}" if alias.asname else ""))
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            names = ", ".join(
                (a.name + (f" as {a.asname}" if a.asname else "")) for a in node.names
            )
            imports.append(f"from {module} import {names}")

    # Top-level functions
    functions = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(_extract_function_info(node))

    # Classes
    classes = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            bases = []
            for b in node.bases:
                try:
                    bases.append(ast.unparse(b))
                except Exception:
                    pass
            methods = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append(_extract_function_info(item))
            classes.append({
                "name": node.name,
                "bases": bases,
                "docstring": _get_docstring(node),
                "methods": methods,
                "lineno": node.lineno,
            })

    return {
        "status": "success",
        "functions_count": len(functions) + sum(len(c["methods"]) for c in classes),
        "classes_count": len(classes),
        "imports": imports,
        "functions": functions,
        "classes": classes,
        "source_code": source_code,
    }


def analyze_python_file(file_path):
    """Backward-compatible: trả về status + counts."""
    with open(file_path, 'r', encoding='utf-8') as f:
        source_code = f.read()
    try:
        tree = ast.parse(source_code)
        functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        return {
            "status": "success",
            "functions_count": len(functions),
            "classes_count": len(classes),
        }
    except SyntaxError as e:
        error_line = e.text.strip() if e.text else "Không rõ"
        return {"status": "syntax_error", "message": f"Lỗi ở dòng {e.lineno}: {error_line}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
