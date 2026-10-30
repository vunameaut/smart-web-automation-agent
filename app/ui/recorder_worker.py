"""QThread Worker để khởi chạy Playwright Codegen trong nền không làm đóng băng giao diện Qt."""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional
from PySide6.QtCore import QThread, Signal

from app.utils.logging_config import get_logger

logger = get_logger("autoweb.recorder_worker")


class RecorderWorker(QThread):
    """Worker chạy Playwright Codegen và phát tín hiệu khi người dùng đóng trình duyệt."""

    started_signal = Signal()
    finished_signal = Signal(str)      # Đường dẫn file python được sinh ra
    error_signal = Signal(str)         # Thông báo lỗi nếu có

    def __init__(self, url: str, output_file: Path, storage_state_path: Optional[Path] = None):
        super().__init__()
        self.url = url.strip() or "about:blank"
        self.output_file = Path(output_file)
        self.storage_state_path = storage_state_path
        self._proc: Optional[subprocess.Popen] = None

    def run(self):
        """Khởi động tiến trình playwright codegen."""
        self.started_signal.emit()
        logger.info(f"Khởi chạy Playwright Codegen với URL: {self.url}...")

        # Đảm bảo thư mục cha tồn tại
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        if self.output_file.exists():
            try:
                self.output_file.unlink()
            except Exception:
                pass

        cmd = [
            sys.executable,
            "-m",
            "playwright",
            "codegen",
            self.url,
            "--target",
            "python",
            "-o",
            str(self.output_file),
        ]

        if self.storage_state_path:
            cmd.extend(["--save-storage", str(self.storage_state_path)])

        try:
            # Khởi chạy subprocess độc lập
            self._proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            stdout, stderr = self._proc.communicate()

            if self.output_file.exists() and self.output_file.stat().st_size > 0:
                logger.info(f"Playwright Codegen hoàn tất. Đã lưu kịch bản vào: {self.output_file}")
                self.finished_signal.emit(str(self.output_file))
            else:
                if self._proc.returncode != 0 and stderr:
                    logger.error(f"Playwright Codegen thất bại: {stderr}")
                    self.error_signal.emit(f"Lỗi khởi chạy trình ghi: {stderr.strip()}")
                else:
                    self.error_signal.emit("Không có thao tác nào được ghi nhận hoặc người dùng đã hủy.")
        except Exception as e:
            logger.error(f"Ngoại lệ khi chạy RecorderWorker: {e}")
            self.error_signal.emit(str(e))

    def stop(self):
        """Dừng tiến trình nếu cần."""
        if self._proc and self._proc.poll() is None:
            try:
                self._proc.terminate()
            except Exception:
                pass
