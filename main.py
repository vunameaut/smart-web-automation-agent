"""Smart Web Automation Agent - Điểm khởi động chính của ứng dụng."""

import sys
import io

# Đảm bảo UTF-8 I/O trên Windows
if sys.platform == "win32":
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import argparse
import asyncio
from app.database.database import init_db
from app.utils.logging_config import get_logger

logger = get_logger("main")


def print_tasks_table():
    """Hiển thị danh sách các nhiệm vụ hiện có trong DB qua CLI."""
    from app.core.task_manager import TaskManager
    tm = TaskManager()
    tasks = tm.list_tasks()
    
    print("\n" + "=" * 90)
    print(f"{'STT':<5} {'TASK ID':<38} {'TÊN NHIỆM VỤ':<30} {'TRẠNG THÁI':<12}")
    print("-" * 90)
    if not tasks:
        print("Chưa có nhiệm vụ nào trong hệ thống. Hãy chạy --demo hoặc mở app để tạo.")
    for i, t in enumerate(tasks, 1):
        status_str = "BẬT" if t.enabled else "TẮT"
        print(f"{i:<5} {t.id:<38} {t.name:<30} {status_str:<12}")
    print("=" * 90)
    print("Mẹo: Sao chép TASK ID ở trên để chạy: python main.py --run-task <TASK_ID>\n")


def main():
    # Khởi tạo SQLite database
    init_db()

    parser = argparse.ArgumentParser(
        description="Smart Web Automation Agent - Local-first browser automation & workflow scheduling."
    )
    parser.add_argument(
        "--list-tasks",
        action="store_true",
        help="Liệt kê danh sách tất cả nhiệm vụ kèm UUID để chạy lệnh",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Chạy kịch bản Demo tương tác Chromium",
    )
    parser.add_argument(
        "--run-task",
        type=str,
        help="ID nhiệm vụ cần chạy ngay qua dòng lệnh (dùng --list-tasks để xem ID)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Chạy ở chế độ an toàn Dry-run (không gửi hành động có rủi ro cao)",
    )

    args = parser.parse_args()

    if args.list_tasks:
        print_tasks_table()
        return

    if args.demo:
        logger.info("Chạy chế độ Demo...")
        from demo_phase1 import run_demo
        asyncio.run(run_demo())
        return

    if args.run_task:
        logger.info(f"Kích hoạt chạy task [{args.run_task}] qua CLI (dry_run={args.dry_run})...")
        from app.core.task_manager import TaskManager
        tm = TaskManager()
        res = asyncio.run(tm.run_now(args.run_task, dry_run=args.dry_run))
        print("\nKết quả thực thi:")
        print(f"Trạng thái: {res.get('status')}")
        if res.get('error'):
            print(f"Lỗi: {res.get('error')}")
        return

    # Mặc định khởi chạy giao diện Desktop UI
    logger.info("Khởi chạy Desktop UI (PySide6)...")
    from app.ui.main_window import run_app
    run_app()


if __name__ == "__main__":
    main()
