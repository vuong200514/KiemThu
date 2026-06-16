"""
reporter.py — Sinh báo cáo HTML cho một lần kiểm thử (1 file hoặc 1 hàm).
Hiển thị: kết quả pytest (pass/fail từng test), statement coverage,
branch coverage, và danh sách dòng/nhánh còn thiếu.
"""

import json
import os


def generate_report(source_file: str, test_file: str, exec_result: dict,
                     func_name: str = None, out_dir: str = "reports") -> str:
    os.makedirs(out_dir, exist_ok=True)

    pytest_output = exec_result.get("output", "")
    coverage = exec_result.get("coverage") or {}
    overall = coverage.get("overall", {})
    files_cov = coverage.get("files", {})

    src_basename = os.path.basename(source_file)
    file_cov = files_cov.get(src_basename, {})

    tests = _parse_test_results(pytest_output)

    suffix = f"_{func_name}" if func_name else ""
    html_path = os.path.join(out_dir, f"report_{src_basename}{suffix}.html")
    json_path = os.path.join(out_dir, f"report_{src_basename}{suffix}.json")

    report_data = {
        "source_file": src_basename,
        "func_name": func_name,
        "status": exec_result.get("status"),
        "tests": tests,
        "coverage_overall": overall,
        "coverage_file": file_cov,
        "pytest_output": pytest_output,
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)

    html = _render_html(report_data)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    return html_path


def _parse_test_results(output: str) -> list:
    tests = []
    for line in output.splitlines():
        line = line.strip()
        for status in ("PASSED", "FAILED", "ERROR"):
            marker = f" {status}"
            if marker in line and "::" in line:
                name = line.split(marker)[0].strip()
                tests.append({"name": name, "status": status})
                break
    return tests


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _render_html(data: dict) -> str:
    tests = data["tests"]
    passed = sum(1 for t in tests if t["status"] == "PASSED")
    failed = sum(1 for t in tests if t["status"] in ("FAILED", "ERROR"))
    total = len(tests)

    stmt_pct = data["coverage_file"].get("statement_coverage_pct", data["coverage_overall"].get("statement_coverage_pct", 0))
    branch_pct = data["coverage_file"].get("branch_coverage_pct", data["coverage_overall"].get("branch_coverage_pct", 0))
    missing_lines = data["coverage_file"].get("missing_lines", [])

    rows = "".join(
        f'<tr class="{"ok" if t["status"]=="PASSED" else "bad"}">'
        f'<td>{_esc(t["name"])}</td><td>{_esc(t["status"])}</td></tr>'
        for t in tests
    ) or '<tr><td colspan="2" class="muted">Không có test nào được phát hiện.</td></tr>'

    title = f"{_esc(data['source_file'])}" + (f" :: {_esc(data['func_name'])}" if data["func_name"] else "")

    return f"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<title>Báo cáo kiểm thử — {title}</title>
<style>
  :root {{ --bg:#0d1117; --panel:#161b22; --border:#30363d; --text:#c9d1d9; --muted:#6e7681;
           --green:#3fb950; --red:#f85149; --accent:#58a6ff; }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: 'Segoe UI', Inter, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 32px; }}
  h1 {{ font-size: 1.3rem; margin-bottom: 4px; }}
  .muted {{ color: var(--muted); }}
  .cards {{ display: flex; gap: 16px; margin: 20px 0; flex-wrap: wrap; }}
  .card {{ background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 16px 20px; min-width: 160px; }}
  .card .num {{ font-size: 1.8rem; font-weight: 700; }}
  .card .label {{ font-size: 0.8rem; color: var(--muted); text-transform: uppercase; letter-spacing: .03em; }}
  .green {{ color: var(--green); }} .red {{ color: var(--red); }} .blue {{ color: var(--accent); }}
  table {{ width: 100%; border-collapse: collapse; background: var(--panel); border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }}
  th, td {{ padding: 10px 14px; text-align: left; border-bottom: 1px solid var(--border); font-size: 0.9rem; }}
  th {{ color: var(--muted); font-weight: 600; }}
  tr.ok td:last-child {{ color: var(--green); font-weight: 600; }}
  tr.bad td:last-child {{ color: var(--red); font-weight: 600; }}
  pre {{ background: #010409; border: 1px solid var(--border); border-radius: 8px; padding: 14px; overflow-x: auto; font-size: 0.82rem; white-space: pre-wrap; }}
  section {{ margin-top: 28px; }}
</style>
</head>
<body>
  <h1>Báo cáo kiểm thử</h1>
  <p class="muted">{title}</p>

  <div class="cards">
    <div class="card"><div class="num {'green' if failed==0 and total>0 else 'red'}">{passed}/{total}</div><div class="label">Test pass</div></div>
    <div class="card"><div class="num blue">{stmt_pct:.1f}%</div><div class="label">Statement coverage</div></div>
    <div class="card"><div class="num blue">{branch_pct:.1f}%</div><div class="label">Branch coverage</div></div>
  </div>

  <section>
    <h3>Kết quả từng test</h3>
    <table><thead><tr><th>Test</th><th>Trạng thái</th></tr></thead><tbody>{rows}</tbody></table>
  </section>

  <section>
    <h3>Dòng chưa được coverage</h3>
    <p class="muted">{_esc(', '.join(str(l) for l in missing_lines)) if missing_lines else 'Không có — 100% statement coverage.'}</p>
  </section>

  <section>
    <h3>Đầu ra Pytest</h3>
    <pre>{_esc(data['pytest_output'])}</pre>
  </section>
</body>
</html>"""


if __name__ == "__main__":
    print("Use generate_report(source_file, test_file, exec_result, func_name=None).")