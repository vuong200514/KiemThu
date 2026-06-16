import ast
import json
import os
import re
import webbrowser
from typing import Dict, List, Tuple


def _module_name_from_path(file_path: str) -> str:
    return os.path.splitext(os.path.basename(file_path))[0]


def analyze_calls(file_path: str) -> Tuple[List[Dict], List[Tuple[str, str]], Dict[str, str], str]:
    """Build AST graph nodes and edges.

    Graph hierarchy:
    - file node
    - class nodes under file
    - function/method nodes under file/class

    Also returns:
    - functions_map: map short names to function node ids
    - module_name: source module name (e.g. sample)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        src = f.read()

    tree = ast.parse(src)
    module = _module_name_from_path(file_path)
    file_label = os.path.basename(file_path)

    nodes: List[Dict] = []
    edges: List[Tuple[str, str]] = []
    functions_map: Dict[str, str] = {}

    file_id = module
    nodes.append({
        'id': file_id,
        'label': file_label,
        'type': 'file',
        'lineno': None,
    })

    id_to_ast: Dict[str, ast.AST] = {}

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            fid = f"{module}::{node.name}"
            nodes.append({
                'id': fid,
                'label': node.name,
                'type': 'function',
                'lineno': getattr(node, 'lineno', None),
            })
            edges.append((file_id, fid))
            functions_map[node.name] = fid
            id_to_ast[fid] = node

        if isinstance(node, ast.ClassDef):
            cid = f"{module}::{node.name}"
            nodes.append({
                'id': cid,
                'label': node.name,
                'type': 'class',
                'lineno': getattr(node, 'lineno', None),
            })
            edges.append((file_id, cid))

            for sub in node.body:
                if isinstance(sub, ast.FunctionDef):
                    mid = f"{cid}::{sub.name}"
                    nodes.append({
                        'id': mid,
                        'label': sub.name,
                        'type': 'method',
                        'lineno': getattr(sub, 'lineno', None),
                    })
                    edges.append((cid, mid))
                    functions_map[sub.name] = mid
                    functions_map[f"{node.name}::{sub.name}"] = mid
                    id_to_ast[mid] = sub

    # Intra-file call edges
    existing_nodes = {n['id'] for n in nodes}
    for caller_id, ast_node in id_to_ast.items():
        for sub in ast.walk(ast_node):
            if not isinstance(sub, ast.Call):
                continue

            callee_id = None
            if isinstance(sub.func, ast.Name):
                callee_id = functions_map.get(sub.func.id)
            elif isinstance(sub.func, ast.Attribute):
                attr = sub.func.attr
                val = sub.func.value
                if isinstance(val, ast.Name) and val.id == module:
                    callee_id = functions_map.get(attr)
                else:
                    callee_id = functions_map.get(attr)

            if callee_id and callee_id in existing_nodes:
                edges.append((caller_id, callee_id))

    return nodes, edges, functions_map, module


def extract_tests(test_file_path: str, functions_map: Dict[str, str], module_name: str) -> Dict[str, Dict]:
    """Extract test functions and map called functions using AST."""
    with open(test_file_path, 'r', encoding='utf-8') as f:
        src = f.read()

    tree = ast.parse(src)
    lines = src.splitlines()
    tests: Dict[str, Dict] = {}

    def _collect_calls(fn_node: ast.FunctionDef) -> List[str]:
        calls: List[str] = []
        for sub in ast.walk(fn_node):
            if not isinstance(sub, ast.Call):
                continue

            func_id = None
            if isinstance(sub.func, ast.Name):
                func_id = functions_map.get(sub.func.id)
            elif isinstance(sub.func, ast.Attribute):
                attr = sub.func.attr
                val = sub.func.value
                if isinstance(val, ast.Name) and val.id == module_name:
                    func_id = functions_map.get(attr)
                else:
                    func_id = functions_map.get(attr)

            if func_id:
                calls.append(func_id)

        # remove duplicates, keep order
        return list(dict.fromkeys(calls))

    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith('test'):
            start = node.lineno - 1
            end = getattr(node, 'end_lineno', node.lineno)
            tests[node.name] = {
                'source': '\n'.join(lines[start:end]),
                'class': None,
                'calls': _collect_calls(node),
            }

        if isinstance(node, ast.ClassDef):
            for sub in node.body:
                if isinstance(sub, ast.FunctionDef) and sub.name.startswith('test'):
                    start = sub.lineno - 1
                    end = getattr(sub, 'end_lineno', sub.lineno)
                    tid = f"{node.name}::{sub.name}"
                    tests[tid] = {
                        'source': '\n'.join(lines[start:end]),
                        'class': node.name,
                        'calls': _collect_calls(sub),
                    }

    return tests


def map_tests_to_functions(tests: Dict[str, Dict], functions_map: Dict[str, str]) -> Dict[str, List[str]]:
    mapping = {fid: [] for fid in set(functions_map.values())}
    for tid, info in tests.items():
        for fid in info.get('calls', []):
            mapping.setdefault(fid, []).append(tid)
    return mapping


def parse_pytest_output(output: str) -> Dict[str, str]:
    """Parse pytest -v output lines into status map by test id and short id."""
    status: Dict[str, str] = {}
    stat_re = re.compile(r'\b(PASSED|FAILED|ERROR|XFAILED|XPASS|skipped)\b')

    for line in output.splitlines():
        sline = line.strip()
        if not sline:
            continue

        m = stat_re.search(sline)
        if not m:
            continue

        stat = m.group(1)
        tokens = sline.split()
        tid = None
        for t in tokens:
            if '::' in t and t.startswith('test_'):
                tid = t
                break
            if t.startswith('test_') and t.endswith('.py'):
                tid = t
                break
            if '::' in t and '.py::' in t:
                tid = t
                break

        if not tid:
            for t in tokens:
                if '::' in t:
                    tid = t
                    break

        if not tid:
            continue

        tid = tid.rstrip(',:')
        status[tid] = stat

        if '::' in tid:
            short = tid.split('::')[-1]
            status[short] = stat

    return status


def _node_color(status_counts: Dict[str, int], ntype: str) -> str:
    if ntype == 'file':
        return '#4f46e5'
    if ntype == 'class':
        return '#0ea5e9'

    if not status_counts:
        return '#9ca3af'

    if status_counts.get('FAILED') or status_counts.get('ERROR'):
        return '#ef4444'

    total = sum(status_counts.values())
    passed = status_counts.get('PASSED', 0)
    if total > 0 and passed == total:
        return '#22c55e'

    return '#f59e0b'


def generate_report(source_file: str, test_file: str, pytest_output: str, out_dir: str = 'reports') -> str:
    os.makedirs(out_dir, exist_ok=True)

    nodes, edges, functions_map, module_name = analyze_calls(source_file)

    tests: Dict[str, Dict] = {}
    test_path = test_file if os.path.exists(test_file) else os.path.join(os.getcwd(), test_file)
    if os.path.exists(test_path):
        tests = extract_tests(test_path, functions_map, module_name)

    mapping = map_tests_to_functions(tests, functions_map)
    statuses = parse_pytest_output(pytest_output or '')

    # annotate nodes
    function_node_ids = set(functions_map.values())
    for n in nodes:
        nid = n['id']
        if nid in function_node_ids:
            ntests = mapping.get(nid, [])
        else:
            ntests = []

        status_counts: Dict[str, int] = {}
        for tid in ntests:
            st = statuses.get(tid) or statuses.get(tid.split('::')[-1]) or 'unknown'
            status_counts[st] = status_counts.get(st, 0) + 1

        n['tests'] = ntests
        n['test_count'] = len(ntests)
        n['status_counts'] = status_counts
        n['color'] = _node_color(status_counts, n.get('type', 'function'))

    report_data = {
        'nodes': nodes,
        'edges': [{'from': a, 'to': b} for a, b in edges],
        'tests': tests,
        'pytest_output': pytest_output,
    }

    json_path = os.path.join(out_dir, f"report_{os.path.basename(source_file)}.json")
    html_path = os.path.join(out_dir, f"report_{os.path.basename(source_file)}.html")

    with open(json_path, 'w', encoding='utf-8') as jf:
        json.dump(report_data, jf, ensure_ascii=False, indent=2)

    json_text = json.dumps(report_data)
    safe_pytest = (pytest_output or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    html_template = '''<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>AutoTestTool Report - {{FNAME}}</title>
  <script type="text/javascript" src="https://unpkg.com/vis-network@9.1.2/dist/vis-network.min.js"></script>
  <link href="https://unpkg.com/vis-network@9.1.2/dist/vis-network.min.css" rel="stylesheet" type="text/css" />
  <style>
    html, body { height: 100%; margin: 0; }
    body { font-family: Arial, sans-serif; display: flex; height: 100vh; }
    #network { width: calc(100% - 460px); height: 100vh; border-right: 1px solid #ddd; }
    #panel { width: 460px; padding: 12px; overflow: auto; height: 100vh; }
    pre { background:#f6f8fa; padding:8px; border-radius:4px; white-space: pre-wrap; }
    .badge { display:inline-block; padding:2px 8px; border-radius:999px; margin-right:6px; font-size:12px; }
    .ok { background:#dcfce7; color:#166534; }
    .bad { background:#fee2e2; color:#991b1b; }
    .unk { background:#e5e7eb; color:#374151; }
  </style>
</head>
<body>
  <div id="network"></div>
  <div id="panel">
    <h3>Node Details</h3>
    <div id="details">Click a node to see tests and results.</div>
    <h4>Pytest Output</h4>
    <pre id="pytest_output">{{PYTEST_OUTPUT}}</pre>
  </div>

  <script>
    const data = {{DATA}};

    const visNodes = data.nodes.map(n => {
      const c = n.color || '#9ca3af';
      const size = n.type === 'file' ? 38 : (n.type === 'class' ? 28 : 20);
      const label = n.type === 'function' || n.type === 'method'
        ? `${n.label}\\n(${n.test_count} tests)`
        : n.label;
      return {
        id: n.id,
        label,
        color: { background: c, border: '#1f2937' },
        shape: n.type === 'file' ? 'box' : 'ellipse',
        font: { color: '#111827' },
        size,
      };
    });

    const visEdges = data.edges.map(e => ({ ...e, arrows: 'to' }));

    const container = document.getElementById('network');
    const network = new vis.Network(
      container,
      { nodes: new vis.DataSet(visNodes), edges: new vis.DataSet(visEdges) },
      {
        layout: { hierarchical: { enabled: true, direction: 'UD', sortMethod: 'directed' } },
        physics: false,
        edges: { smooth: false },
      }
    );

    network.on('click', function(params) {
      if (!params.nodes || params.nodes.length === 0) return;
      const id = params.nodes[0];
      const node = data.nodes.find(n => n.id === id);
      const details = document.getElementById('details');

      let html = `<h4>${escapeHtml(id)}</h4>`;
      html += `<div>Type: <b>${escapeHtml(node.type || 'function')}</b></div>`;
      html += `<div>Line: <b>${node.lineno || 'N/A'}</b></div>`;
      html += `<div>Tests: <b>${node.test_count || 0}</b></div>`;

      const counts = node.status_counts || {};
      const passed = counts.PASSED || 0;
      const failed = (counts.FAILED || 0) + (counts.ERROR || 0);
      const unknown = counts.unknown || 0;
      html += `<div style="margin-top:8px;">`;
      html += `<span class="badge ok">PASS: ${passed}</span>`;
      html += `<span class="badge bad">FAIL/ERR: ${failed}</span>`;
      html += `<span class="badge unk">UNKNOWN: ${unknown}</span>`;
      html += `</div>`;

      const tests = node.tests || [];
      if (tests.length > 0) {
        html += '<hr/><h4>Test Cases</h4><ul>';
        for (const tid of tests) {
          const t = data.tests[tid] || { source: 'N/A' };
          const short = tid.includes('::') ? tid.split('::').slice(-1)[0] : tid;
          const st = countsFromOutput(tid, short);
          html += `<li><b>${escapeHtml(tid)}</b> - <i>${escapeHtml(st)}</i><pre>${escapeHtml(t.source || '')}</pre></li>`;
        }
        html += '</ul>';
      } else {
        html += '<hr/><div>No mapped tests for this node.</div>';
      }

      details.innerHTML = html;
    });

    function countsFromOutput(tid, short) {
      const text = data.pytest_output || '';
      if (text.includes(tid + ' PASSED') || text.includes(short + ' PASSED')) return 'PASSED';
      if (text.includes(tid + ' FAILED') || text.includes(short + ' FAILED')) return 'FAILED';
      if (text.includes(tid + ' ERROR') || text.includes(short + ' ERROR')) return 'ERROR';
      return 'unknown';
    }

    function escapeHtml(s) {
      return String(s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
    }
  </script>
</body>
</html>
'''

    html = html_template.replace('{{DATA}}', json_text)
    html = html.replace('{{PYTEST_OUTPUT}}', safe_pytest)
    html = html.replace('{{FNAME}}', os.path.basename(source_file))

    with open(html_path, 'w', encoding='utf-8') as hf:
        hf.write(html)

    try:
        webbrowser.open('file://' + os.path.abspath(html_path))
    except Exception:
        pass

    return html_path


if __name__ == '__main__':
    print('Use generate_report(source_file, test_file, pytest_output).')
