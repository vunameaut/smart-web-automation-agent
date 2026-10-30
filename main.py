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


def main():
    # Khởi tạo SQLite database
    init_db()

    parser = argparse.ArgumentParser(
        description="Smart Web Automation Agent - Local-first browser automation & workflow scheduling."
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Chạy ở chế độ Command Line Interface thay vì mở Desktop UI",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Chạy kịch bản Demo Phase 1",
    )
    parser.add_argument(
        "--run-task",
        type=str,
        help="ID nhiệm vụ cần chạy ngay qua dòng lệnh",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Chạy ở chế độ an toàn Dry-run (không gửi hành động có rủi ro cao)",
    )

    args = parser.parse_args()

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
        print("Kết quả:", res)
        return

    # Mặc định khởi chạy giao diện Desktop UI
    logger.info("Khởi chạy Desktop UI (PySide6)...")
    from app.ui.main_window import run_app
    run_app()


if __name__ == "__main__":
    main()

