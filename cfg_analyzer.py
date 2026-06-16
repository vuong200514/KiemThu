"""
cfg_analyzer.py — Control Flow Graph (CFG) builder cho Python source code.

Chức năng:
- Chế độ OVERVIEW: quét toàn bộ file, hiển thị các hàm/class dưới dạng đồ thị
- Chế độ CFG: vẽ CFG chi tiết cho một hàm cụ thể (nhánh True/False, loop, exception)
"""

import ast
import os
from typing import Dict, List, Optional, Tuple


# ──────────────────────────────────────────────
# DATA STRUCTURES
# ──────────────────────────────────────────────

class CFGNode:
    def __init__(self, node_id: str, label: str, node_type: str,
                 lineno: Optional[int] = None, end_lineno: Optional[int] = None):
        self.id = node_id
        self.label = label          # text hiển thị
        self.type = node_type       # 'entry','exit','statement','condition','loop','exception','return'
        self.lineno = lineno
        self.end_lineno = end_lineno

    def to_dict(self):
        return {
            "id": self.id,
            "label": self.label,
            "type": self.type,
            "lineno": self.lineno,
            "end_lineno": self.end_lineno,
        }


class CFGEdge:
    def __init__(self, from_id: str, to_id: str, label: str = ""):
        self.from_id = from_id
        self.to_id = to_id
        self.label = label   # "", "True", "False", "Loop", "Break", "Exception"

    def to_dict(self):
        return {"from": self.from_id, "to": self.to_id, "label": self.label}


# ──────────────────────────────────────────────
# OVERVIEW MODE — toàn bộ file
# ──────────────────────────────────────────────

def build_overview(file_path: str) -> Dict:
    """
    Quét toàn bộ file Python, trả về nodes/edges ở mức hàm & class.
    Node quan trọng: file root, class, function, async_function.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return {"status": "error", "message": f"Lỗi cú pháp dòng {e.lineno}: {e.msg}"}

    module = os.path.splitext(os.path.basename(file_path))[0]
    nodes = []
    edges = []

    # File root node
    nodes.append({
        "id": module,
        "label": os.path.basename(file_path),
        "type": "file",
        "lineno": None,
        "functions": []
    })

    # Duyệt top-level — chỉ lấy trực tiếp tree.body để tránh nhầm nested
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            cid = f"{module}::{node.name}"
            nodes.append({
                "id": cid,
                "label": node.name,
                "type": "class",
                "lineno": node.lineno,
                "functions": []
            })
            edges.append({"from": module, "to": cid, "label": ""})

            # Methods trong class (chỉ body trực tiếp, không đệ quy)
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    mid = f"{cid}::{item.name}"
                    ftype = "async_function" if isinstance(item, ast.AsyncFunctionDef) else "function"
                    complexity = _cyclomatic_complexity(item)
                    nodes.append({
                        "id": mid,
                        "label": item.name,
                        "type": ftype,
                        "lineno": item.lineno,
                        "end_lineno": getattr(item, "end_lineno", None),
                        "complexity": complexity,
                        "functions": []
                    })
                    edges.append({"from": cid, "to": mid, "label": ""})

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Top-level functions — lấy trực tiếp từ tree.body, không cần check parent
            fid = f"{module}::{node.name}"
            ftype = "async_function" if isinstance(node, ast.AsyncFunctionDef) else "function"
            complexity = _cyclomatic_complexity(node)
            nodes.append({
                "id": fid,
                "label": node.name,
                "type": ftype,
                "lineno": node.lineno,
                "end_lineno": getattr(node, "end_lineno", None),
                "complexity": complexity,
                "functions": []
            })
            edges.append({"from": module, "to": fid, "label": ""})

    # Loại trùng nodes (ast.walk có thể trả về nhiều lần)
    seen = set()
    unique_nodes = []
    for n in nodes:
        if n["id"] not in seen:
            seen.add(n["id"])
            unique_nodes.append(n)

    seen_edges = set()
    unique_edges = []
    for e in edges:
        key = (e["from"], e["to"])
        if key not in seen_edges:
            seen_edges.add(key)
            unique_edges.append(e)

    return {
        "status": "success",
        "mode": "overview",
        "module": module,
        "nodes": unique_nodes,
        "edges": unique_edges,
    }


def _cyclomatic_complexity(func_node) -> int:
    """Tính cyclomatic complexity đơn giản: 1 + số nhánh."""
    count = 1
    for node in ast.walk(func_node):
        if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                              ast.With, ast.Assert, ast.comprehension)):
            count += 1
        elif isinstance(node, ast.BoolOp):
            count += len(node.values) - 1
    return count


# ──────────────────────────────────────────────
# CFG MODE — chi tiết một hàm
# ──────────────────────────────────────────────

class _CFGBuilder(ast.NodeVisitor):
    """Xây dựng CFG cho một hàm duy nhất."""

    def __init__(self, func_name: str):
        self.func_name = func_name
        self.nodes: List[CFGNode] = []
        self.edges: List[CFGEdge] = []
        self._counter = 0
        self._current: Optional[str] = None   # node id hiện tại

    def _new_id(self, prefix="n") -> str:
        self._counter += 1
        return f"{prefix}_{self._counter}"

    def _add_node(self, label: str, ntype: str,
                  lineno=None, end_lineno=None) -> str:
        nid = self._new_id(ntype)
        self.nodes.append(CFGNode(nid, label, ntype, lineno, end_lineno))
        return nid

    def _add_edge(self, from_id: str, to_id: str, label: str = ""):
        if from_id and to_id:
            self.edges.append(CFGEdge(from_id, to_id, label))

    def build(self, func_node) -> Dict:
        # ENTRY
        params = [arg.arg for arg in func_node.args.args]
        param_str = ", ".join(params) if params else ""
        entry_id = self._add_node(
            f"ENTRY\n{func_node.name}({param_str})", "entry", func_node.lineno
        )
        self._current = entry_id

        exits = self._process_body(func_node.body)

        # EXIT node
        exit_id = self._add_node("EXIT", "exit")
        for eid in exits:
            self._add_edge(eid, exit_id)

        return {
            "status": "success",
            "mode": "cfg",
            "func_name": func_node.name,
            "lineno": func_node.lineno,
            "end_lineno": getattr(func_node, "end_lineno", None),
            "complexity": _cyclomatic_complexity(func_node),
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
        }

    def _process_body(self, stmts) -> List[str]:
        """Xử lý list statements, trả về list node ids 'còn sống' (chưa exit)."""
        live = [self._current]  # điểm vào của block này

        for stmt in stmts:
            new_live = []
            for entry_node in live:
                self._current = entry_node
                exits = self._process_stmt(stmt)
                new_live.extend(exits)
            live = new_live

        return live

    def _process_stmt(self, stmt) -> List[str]:
        """Xử lý một statement, trả về danh sách exit nodes."""
        if isinstance(stmt, ast.If):
            return self._process_if(stmt)
        elif isinstance(stmt, (ast.While,)):
            return self._process_while(stmt)
        elif isinstance(stmt, ast.For):
            return self._process_for(stmt)
        elif isinstance(stmt, ast.Try):
            return self._process_try(stmt)
        elif isinstance(stmt, (ast.Return,)):
            return self._process_return(stmt)
        elif isinstance(stmt, ast.Raise):
            return self._process_raise(stmt)
        elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            # Nested def — chỉ hiện là 1 node
            label = f"def {stmt.name}(...)" if hasattr(stmt, "name") else "nested def"
            nid = self._add_node(label, "statement",
                                  stmt.lineno, getattr(stmt, "end_lineno", None))
            self._add_edge(self._current, nid)
            return [nid]
        else:
            return self._process_simple(stmt)

    def _stmt_label(self, stmt) -> str:
        """Tạo label ngắn gọn cho statement."""
        if isinstance(stmt, ast.Assign):
            targets = ", ".join(ast.unparse(t) for t in stmt.targets)
            return f"{targets} = {ast.unparse(stmt.value)}"
        elif isinstance(stmt, ast.AugAssign):
            op = type(stmt.op).__name__.replace("Add", "+=").replace("Sub", "-=") \
                                        .replace("Mult", "*=").replace("Div", "/=")
            return f"{ast.unparse(stmt.target)} {op} {ast.unparse(stmt.value)}"
        elif isinstance(stmt, ast.Expr):
            return ast.unparse(stmt.value)
        elif isinstance(stmt, ast.Import):
            return f"import {', '.join(a.name for a in stmt.names)}"
        elif isinstance(stmt, ast.ImportFrom):
            return f"from {stmt.module} import ..."
        elif isinstance(stmt, ast.Delete):
            return f"del {', '.join(ast.unparse(t) for t in stmt.targets)}"
        elif isinstance(stmt, ast.Assert):
            return f"assert {ast.unparse(stmt.test)}"
        elif isinstance(stmt, ast.Global):
            return f"global {', '.join(stmt.names)}"
        elif isinstance(stmt, ast.Nonlocal):
            return f"nonlocal {', '.join(stmt.names)}"
        elif isinstance(stmt, ast.Pass):
            return "pass"
        elif isinstance(stmt, ast.Break):
            return "break"
        elif isinstance(stmt, ast.Continue):
            return "continue"
        else:
            try:
                return ast.unparse(stmt)[:60]
            except Exception:
                return type(stmt).__name__

    def _process_simple(self, stmt) -> List[str]:
        label = self._stmt_label(stmt)
        # Cắt nhãn dài
        if len(label) > 50:
            label = label[:47] + "..."
        nid = self._add_node(label, "statement",
                              stmt.lineno, getattr(stmt, "end_lineno", None))
        self._add_edge(self._current, nid)
        return [nid]

    def _process_if(self, stmt: ast.If) -> List[str]:
        cond = ast.unparse(stmt.test)
        if len(cond) > 40:
            cond = cond[:37] + "..."
        cond_id = self._add_node(f"if {cond}", "condition", stmt.lineno)
        self._add_edge(self._current, cond_id)

        # TRUE branch
        self._current = cond_id
        true_exits = self._process_body(stmt.body)
        for e in true_exits:
            # mark edge label True đã có trong _process_body, cần patch lại
            pass
        # Patch: thêm label True lên edge từ cond_id → first node của body
        self._patch_edge_label(cond_id, "True")

        # FALSE / elif branch
        false_exits = []
        if stmt.orelse:
            self._current = cond_id
            false_exits = self._process_body(stmt.orelse)
            self._patch_edge_label(cond_id, "False")
        else:
            # Không có else → edge False đi thẳng ra ngoài
            false_exits = [cond_id]
            # Tạo edge giả để vis-network biết nhánh False
            skip_id = self._add_node("(skip)", "statement", stmt.lineno)
            self._add_edge(cond_id, skip_id, "False")
            false_exits = [skip_id]

        return true_exits + false_exits

    def _patch_edge_label(self, from_id: str, label: str):
        """Gán label cho edge mới nhất từ from_id."""
        for edge in reversed(self.edges):
            if edge.from_id == from_id and edge.label == "":
                edge.label = label
                break

    def _process_while(self, stmt: ast.While) -> List[str]:
        cond = ast.unparse(stmt.test)
        if len(cond) > 40:
            cond = cond[:37] + "..."
        cond_id = self._add_node(f"while {cond}", "loop", stmt.lineno)
        self._add_edge(self._current, cond_id)

        # Body — back edges quay về cond (True branch)
        self._current = cond_id
        body_exits = self._process_body(stmt.body)
        for e in body_exits:
            self._add_edge(e, cond_id, "Loop")  # back edge
        # Label edge đầu tiên từ cond → body là "True"
        self._patch_edge_label(cond_id, "True")

        # False exit: tạo node "exit loop" để vis-network hiển thị nhánh False rõ ràng
        exit_loop_id = self._add_node("(exit loop)", "statement", stmt.end_lineno if hasattr(stmt, "end_lineno") else stmt.lineno)
        self._add_edge(cond_id, exit_loop_id, "False")

        # orelse (while-else)
        if stmt.orelse:
            self._current = exit_loop_id
            else_exits = self._process_body(stmt.orelse)
            return else_exits

        return [exit_loop_id]

    def _process_for(self, stmt: ast.For) -> List[str]:
        target = ast.unparse(stmt.target)
        iter_ = ast.unparse(stmt.iter)
        if len(iter_) > 30:
            iter_ = iter_[:27] + "..."
        loop_id = self._add_node(f"for {target} in {iter_}", "loop", stmt.lineno)
        self._add_edge(self._current, loop_id)

        # Body — back edges quay về loop (Iterate)
        self._current = loop_id
        body_exits = self._process_body(stmt.body)
        for e in body_exits:
            self._add_edge(e, loop_id, "Next")
        self._patch_edge_label(loop_id, "Iterate")

        # Done exit — khi hết iterator
        exit_loop_id = self._add_node("(exit loop)", "statement",
                                      getattr(stmt, "end_lineno", stmt.lineno))
        self._add_edge(loop_id, exit_loop_id, "Done")

        # orelse (for-else)
        if stmt.orelse:
            self._current = exit_loop_id
            else_exits = self._process_body(stmt.orelse)
            return else_exits

        return [exit_loop_id]

    def _process_try(self, stmt: ast.Try) -> List[str]:
        try_id = self._add_node("try", "exception", stmt.lineno)
        self._add_edge(self._current, try_id)

        # Body
        self._current = try_id
        body_exits = self._process_body(stmt.body)

        all_exits = []

        # Except handlers
        for handler in stmt.handlers:
            exc_label = f"except {ast.unparse(handler.type) if handler.type else 'Exception'}"
            exc_id = self._add_node(exc_label, "exception",
                                    handler.lineno)
            self._add_edge(try_id, exc_id, "Exception")
            self._current = exc_id
            h_exits = self._process_body(handler.body)
            all_exits.extend(h_exits)

        # Else (no exception)
        if stmt.orelse:
            self._current = try_id
            for e in body_exits:
                self._current = e
            else_exits = self._process_body(stmt.orelse)
            all_exits.extend(else_exits)
        else:
            all_exits.extend(body_exits)

        # Finally — Python AST dùng `finalbody`, không phải `finalbody`
        finalbody = getattr(stmt, "finalbody", None)
        if finalbody:
            finally_id = self._add_node("finally", "exception",
                                         getattr(stmt, "lineno", None))
            for e in all_exits:
                self._add_edge(e, finally_id)
            self._current = finally_id
            final_exits = self._process_body(finalbody)
            return final_exits

        return all_exits

    def _process_return(self, stmt: ast.Return) -> List[str]:
        val = ast.unparse(stmt.value) if stmt.value else "None"
        if len(val) > 40:
            val = val[:37] + "..."
        nid = self._add_node(f"return {val}", "return", stmt.lineno)
        self._add_edge(self._current, nid)
        return [nid] # Sửa trả về node ID thay vì []

    def _process_raise(self, stmt: ast.Raise) -> List[str]:
        val = ast.unparse(stmt.exc) if stmt.exc else "re-raise"
        nid = self._add_node(f"raise {val}", "exception", stmt.lineno)
        self._add_edge(self._current, nid)
        return []


def build_cfg(file_path: str, func_name: str) -> Dict:
    """
    Xây dựng CFG cho hàm func_name trong file_path.
    Tìm hàm ở cả top-level lẫn bên trong class.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return {"status": "error", "message": f"Lỗi cú pháp: {e}"}

    # Tìm hàm theo tên
    target = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == func_name:
                target = node
                break

    if target is None:
        return {"status": "error", "message": f"Không tìm thấy hàm '{func_name}'"}

    builder = _CFGBuilder(func_name)
    return builder.build(target)


# ──────────────────────────────────────────────
# PUBLIC API
# ──────────────────────────────────────────────

def analyze_file(file_path: str, mode: str = "overview",
                 func_name: Optional[str] = None) -> Dict:
    """
    Entry point cho API.

    mode="overview" → trả về đồ thị tổng quan toàn file
    mode="cfg"      → trả về CFG chi tiết cho func_name
    """
    if not os.path.exists(file_path):
        return {"status": "error", "message": f"Không tìm thấy file: {file_path}"}

    if mode == "cfg":
        if not func_name:
            return {"status": "error", "message": "Cần truyền func_name khi mode=cfg"}
        return build_cfg(file_path, func_name)
    else:
        return build_overview(file_path)