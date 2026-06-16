import argparse
import os
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Các module do chúng ta tự viết (phải đảm bảo 3 file này nằm cùng thư mục)
from analyzer import analyze_python_file
from ai_generator import generate_test_cases
from executor import run_test_file
from reporter import generate_report

# Khởi tạo công cụ giao diện
console = Console()

def main():
    welcome_message = Panel.fit(
        "[bold cyan]Chào mừng đến với AutoTestTool[/bold cyan]\n"
        "[green]Hệ thống kiểm thử mã nguồn tự động thông minh[/green]",
        title="Bắt đầu",
        border_style="cyan"
    )
    console.print(welcome_message)

    parser = argparse.ArgumentParser(description="Tool kiểm thử tự động")
    parser.add_argument("file_path", help="Đường dẫn đến file source code cần test")
    args = parser.parse_args()
    target_file = args.file_path

    if not os.path.exists(target_file):
        console.print(f"[bold red]Lỗi: Không tìm thấy file '{target_file}'![/bold red]")
        return

    console.print(f"\n[bold green]Đã tìm thấy file:[/bold green] {target_file}\n")







    console.print("[yellow]Đang phân tích mã tĩnh (Static Analysis)...[/yellow]")
    result = analyze_python_file(target_file)

    if result["status"] == "success":
        # Vẽ bảng kết quả
        table = Table(title="[bold magenta]Báo Cáo Phân Tích Code[/bold magenta]")
        table.add_column("Chỉ số", justify="left", style="cyan", no_wrap=True)
        table.add_column("Số lượng", justify="center", style="green")

        table.add_row("Số lượng Hàm (Functions)", str(result["functions_count"]))
        table.add_row("Số lượng Lớp (Classes)", str(result["classes_count"]))

        console.print(table)
        console.print("[bold green]Code không có lỗi cú pháp cơ bản![/bold green]\n")
        









        console.print("[yellow]🤖 Đang gọi AI để sinh Test Case tự động...[/yellow]")
        ai_result = generate_test_cases(target_file)
        
        if ai_result["status"] == "success":
            # Tạo file test mới
            test_file_name = f"test_{os.path.basename(target_file)}"
            
            with open(test_file_name, "w", encoding="utf-8") as f:
                f.write(ai_result["test_code"])
            
            console.print(f"[bold green]✨ Phép thuật đã thành công![/bold green] Đã lưu test case vào file: [cyan]{test_file_name}[/cyan]\n")
            






            console.print("[yellow]⚙️ Đang đưa test case vào buồng đốt (Execution Engine)...[/yellow]")
            exec_result = run_test_file(test_file_name)
            
            # Đánh giá kết quả chạy test
            if exec_result["status"] == "passed":
                console.print(Panel.fit(
                    "[bold green]🏆 KẾT QUẢ: MÃ NGUỒN HOÀN HẢO![/bold green]\n"
                    "Tất cả các test case AI sinh ra đều PASS.",
                    border_style="green"
                ))
            elif exec_result["status"] == "failed":
                console.print(Panel.fit(
                    "[bold red]💥 KẾT QUẢ: PHÁT HIỆN LỖI (FAIL)[/bold red]\n"
                    "Mã nguồn không vượt qua được một số test case.",
                    border_style="red"
                ))
            else:
                console.print("[bold red]🚨 Lỗi hệ thống khi chạy test (Có thể AI sinh code test bị sai cú pháp).[/bold red]")
            



            console.print("\n[bold cyan]📄 CHI TIẾT BÀI TEST:[/bold cyan]")
            console.print(exec_result["output"])
            



            if exec_result["error_log"]:
                console.print(f"[red]{exec_result['error_log']}[/red]")
            try:
                html_path = generate_report(target_file, test_file_name, exec_result.get('output', ''))
                console.print(f"[bold green] Báo cáo tương tác đã được tạo:[/bold green] {html_path}")
            except Exception as e:
                console.print(f"[bold red]❌ Lỗi khi tạo báo cáo: {e}[/bold red]")
                
        else:
            console.print(f"[bold red]❌ AI gặp lỗi: {ai_result['message']}[/bold red]\n")

    elif result["status"] == "syntax_error":
        console.print("[bold red]PHÁT HIỆN LỖI CÚ PHÁP NGHIÊM TRỌNG TRONG FILE GỐC[/bold red]")
        console.print(f"[red]Chi tiết: {result['message']}[/red]\n")
    else:
        console.print(f"[bold red]❌ Lỗi không xác định: {result['message']}[/bold red]\n")

if __name__ == "__main__":
    main()