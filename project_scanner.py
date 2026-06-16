"""
project_scanner.py — Quét toàn bộ thư mục Python, xây dựng graph tổng quan
đã lọc bỏ node rối (private, trivial, __dunder__), trả về nodes/edges cho vis-network.
"""

import ast
import os
import glob


_MIN_COMPLEXITY = 1   # bỏ hàm complexity == 1 VÀ là private / dunder
_SKIP_NAMES = {"__init_subclass__", "__class_getitem__", "__repr__", "__str__"}


def _cyclomatic(func_node) -> int:
    count = 1
    for node in ast.walk(func_node):
        if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                              ast.With, ast.Assert, ast.comprehension)):
            count += 1
        elif isinstance(node, ast.BoolOp):
            count += len(node.values) - 1
    return count


def _should_skip(name: str, complexity: int) -> bool:
    if name in _SKIP_NAMES:
        return True
    is_dunder = name.startswith("__") and name.endswith("__")
    is_private = name.startswith("_") and not name.startswith("__")
    # bỏ dunder nếu không phải __init__ với complexity > 1
    if is_dunder and not (name == "__init__" and complexity > 1):
        return True
    # bỏ private có complexity == 1 (hàm helper đơn giản)
    if is_private and complexity <= _MIN_COMPLEXITY:
        return True
    return False


def scan_project(dir_path: str) -> dict:
    """
    Quét toàn bộ thư mục dir_path (đệ quy), trả về:
    - nodes: list node (file, class, function, method)
    - edges: list edge
    - file_count, node_count
    """
    if not os.path.isdir(dir_path):
        return {"status": "error", "message": f"Thư mục không tồn tại: {dir_path}"}

    py_files = [
        f for f in glob.glob(os.path.join(dir_path, "**/*.py"), recursive=True)
        if not any(f"/{skip}/" in f or f"\\{skip}\\" in f
                   for skip in (".venv", "venv", "__pycache__", ".git",
                                "node_modules", ".tox", "dist/", "site-packages"))
        and not os.path.basename(f).startswith("test_")
    ]

    nodes = []
    edges = []
    file_count = 0

    for file_path in sorted(py_files):
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
                source = fh.read()
            tree = ast.parse(source)
        except Exception:
            continue

        rel = os.path.relpath(file_path, dir_path)
        fid = f"file::{rel}"

        # count importable functions for the file node
        top_fns = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        top_cls = [n for n in tree.body if isinstance(n, ast.ClassDef)]
        nodes.append({
            "id": fid,
            "label": os.path.basename(file_path),
            "type": "file",
            "file_path": file_path,
            "lineno": None,
        })
        file_count += 1

        # top-level functions
        for fn in top_fns:
            cx = _cyclomatic(fn)
            if _should_skip(fn.name, cx):
                continue
            ftype = "async_function" if isinstance(fn, ast.AsyncFunctionDef) else "function"
            nid = f"{fid}::{fn.name}"
            nodes.append({
                "id": nid, "label": fn.name, "type": ftype,
                "file_path": file_path, "lineno": fn.lineno,
                "end_lineno": getattr(fn, "end_lineno", None),
                "complexity": cx, "is_private": fn.name.startswith("_"),
            })
            edges.append({"from": fid, "to": nid, "label": ""})

        # classes
        for cls in top_cls:
            cid = f"{fid}::{cls.name}"
            nodes.append({
                "id": cid, "label": cls.name, "type": "class",
                "file_path": file_path, "lineno": cls.lineno,
            })
            edges.append({"from": fid, "to": cid, "label": ""})

            for m in cls.body:
                if not isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                cx = _cyclomatic(m)
                if _should_skip(m.name, cx):
                    continue
                mtype = "async_method" if isinstance(m, ast.AsyncFunctionDef) else "method"
                mid = f"{cid}::{m.name}"
                nodes.append({
                    "id": mid, "label": m.name, "type": mtype,
                    "file_path": file_path, "lineno": m.lineno,
                    "end_lineno": getattr(m, "end_lineno", None),
                    "complexity": cx, "is_private": m.name.startswith("_"),
                })
                edges.append({"from": cid, "to": mid, "label": ""})

    return {
        "status": "success",
        "root_dir": dir_path,
        "file_count": file_count,
        "node_count": len(nodes),
        "nodes": nodes,
        "edges": edges,
        "errors": [],
    }
