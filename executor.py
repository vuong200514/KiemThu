import subprocess
import sys
import os
import json


PYTEST_TIMEOUT_SECONDS = int(os.getenv("PYTEST_TIMEOUT_SECONDS", "60"))


def run_test_file(test_file_path: str, source_file_path: str = None) -> dict:
    """
    Chạy pytest qua coverage.py (--branch) để đo cả statement coverage và
    branch coverage trên file nguồn tương ứng. Trả về kết quả thực thi + coverage.
    """
    try:
        test_abs = os.path.abspath(test_file_path)
        test_dir = os.path.dirname(test_abs)
        cov_data_file = os.path.join(test_dir, f".coverage_{os.path.basename(test_abs)}")

        cov_include = "*"
        if source_file_path:
            cov_include = os.path.abspath(source_file_path)

        env = os.environ.copy()
        env["COVERAGE_FILE"] = cov_data_file
        env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
        env["PYTHONDONTWRITEBYTECODE"] = "1"

        run_cmd = [
            sys.executable, "-m", "coverage", "run", "--branch",
            f"--include={cov_include}",
            "-m", "pytest", test_abs, "-v", "--tb=short",
            "--import-mode=importlib",
        ]
        result = subprocess.run(
            run_cmd,
            capture_output=True,
            text=True,
            cwd=test_dir,
            env=env,
            timeout=PYTEST_TIMEOUT_SECONDS,
        )

        if result.returncode == 0:
            status = "passed"
        elif result.returncode == 1:
            status = "failed"
        else:
            status = "error"

        output = _combine_output(result.stdout, result.stderr)

        coverage_summary = _get_coverage_json(test_dir, env, cov_data_file)

        try:
            os.remove(cov_data_file)
        except OSError:
            pass

        return {
            "status": status,
            "output": output,
            "error_log": result.stderr,
            "coverage": coverage_summary,
        }

    except subprocess.TimeoutExpired as e:
        output = _combine_output(e.stdout, e.stderr)
        timeout_msg = f"Pytest timeout after {PYTEST_TIMEOUT_SECONDS} seconds."
        if output:
            timeout_msg += "\n\n" + output
        return {
            "status": "error",
            "message": timeout_msg,
            "output": timeout_msg,
            "error_log": _combine_output("", e.stderr),
            "coverage": None,
        }
    except Exception as e:
        error_str = f"Lỗi thực thi: {str(e)}"
        return {"status": "error", "message": error_str, "output": error_str, "coverage": None}


def _combine_output(stdout, stderr) -> str:
    stdout = stdout.decode(errors="replace") if isinstance(stdout, bytes) else (stdout or "")
    stderr = stderr.decode(errors="replace") if isinstance(stderr, bytes) else (stderr or "")
    if stdout and stderr:
        return stdout.rstrip() + "\n\n[stderr]\n" + stderr
    return stdout or stderr


def _get_coverage_json(cwd: str, env: dict, cov_data_file: str) -> dict:
    """Gọi `coverage json` để lấy số liệu statement + branch coverage dạng dict."""
    if not os.path.exists(cov_data_file):
        return None
    try:
        json_out = os.path.join(cwd, f"_covtmp_{os.path.basename(cov_data_file)}.json")
        subprocess.run(
            [sys.executable, "-m", "coverage", "json", "-o", json_out],
            capture_output=True, text=True, cwd=cwd, env=env,
        )
        if not os.path.exists(json_out):
            return None
        with open(json_out, "r", encoding="utf-8") as f:
            data = json.load(f)
        os.remove(json_out)

        files_summary = {}
        for fname, finfo in data.get("files", {}).items():
            s = finfo.get("summary", {})
            files_summary[os.path.basename(fname)] = {
                "statement_coverage_pct": s.get("percent_covered", 0.0),
                "num_statements": s.get("num_statements", 0),
                "missing_lines": finfo.get("missing_lines", []),
                "covered_lines": finfo.get("executed_lines", []),
                "num_branches": s.get("num_branches", 0),
                "num_partial_branches": s.get("num_partial_branches", 0),
                "missing_branches": s.get("num_branches", 0) - s.get("covered_branches", 0)
                                    if s.get("num_branches") else 0,
                "branch_coverage_pct": (
                    round(100.0 * s.get("covered_branches", 0) / s.get("num_branches", 1), 2)
                    if s.get("num_branches") else 100.0
                ),
            }

        totals = data.get("totals", {})
        return {
            "files": files_summary,
            "overall": {
                "statement_coverage_pct": totals.get("percent_covered", 0.0),
                "num_statements": totals.get("num_statements", 0),
                "num_branches": totals.get("num_branches", 0),
                "branch_coverage_pct": (
                    round(100.0 * totals.get("covered_branches", 0) / totals.get("num_branches", 1), 2)
                    if totals.get("num_branches") else 100.0
                ),
            },
        }
    except Exception:
        return None
