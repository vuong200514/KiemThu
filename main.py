import argparse
import os
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from analyzer import analyze_python_file

# Khởi tạo công cụ giao diện
console = Console()

def main():
    # =========================================================
    # GIAI ĐOẠN 0: GIAO DIỆN CHÀO MỪNG & NHẬN FILE
    # =========================================================
    welcome_message = Panel.fit(
        "[bold cyan]🚀 Chào mừng đến với AutoTestTool 🚀[/bold cyan]\n"
        "[green]Hệ thống kiểm thử mã nguồn tự động thông minh[/green]",
        title="Bắt đầu",
        border_style="cyan"
    )
    console.print(welcome_message)

    # Cấu hình nhận đường dẫn file từ dòng lệnh
    parser = argparse.ArgumentParser(description="Tool kiểm thử tự động")
    parser.add_argument("file_path", help="Đường dẫn đến file source code cần test")
    args = parser.parse_args()
    target_file = args.file_path

    # Kiểm tra file có tồn tại không
    if not os.path.exists(target_file):
        console.print(f"[bold red]❌ Lỗi: Không tìm thấy file '{target_file}'![/bold red]")
        return

    console.print(f"\n[bold green]✅ Đã tìm thấy file:[/bold green] {target_file}\n")

if __name__ == "__main__":
    main()