import logging
import re
from typing import Optional
from app.config import get_settings

# Biểu thức regex lọc thông tin nhạy cảm
SENSITIVE_PATTERNS = [
    re.compile(r'(password|passwd|pwd|secret|token|api[_-]?key)["\']?\s*[:=]\s*["\']?([^"\'\s]+)["\']?', re.IGNORECASE),
    re.compile(r'(Bearer\s+)[A-Za-z0-9\-._~+/]+=*', re.IGNORECASE),
]


class SensitiveDataFilter(logging.Filter):
    """Filter tự động làm mờ (mask) mật khẩu, secret, token trong log message."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            msg = record.msg
            for pattern in SENSITIVE_PATTERNS:
                msg = pattern.sub(r'\1: [REDACTED]', msg)
            record.msg = msg
        return True


def setup_logger(name: str = "autoweb") -> logging.Logger:
    """Khởi tạo và cấu hình Logger tập trung cho toàn ứng dụng."""
    settings = get_settings()
    logger = logging.getLogger(name)

    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Tránh gắn handler lặp lại nếu đã khởi tạo
    if logger.handlers:
        return logger

    # Định dạng log chuẩn ISO-8601
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s:%(funcName)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S"
    )

    sensitive_filter = SensitiveDataFilter()

    # Console Handler (hỗ trợ hiển thị terminal)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(sensitive_filter)
    logger.addHandler(console_handler)

    # File Handler (Lưu vào thư mục logs/, ép mã hóa utf-8 trên Windows)
    log_file_path = settings.LOGS_DIR / settings.LOG_FILE_NAME
    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(sensitive_filter)
    logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "autoweb") -> logging.Logger:
    """Lấy logger đã cấu hình hoặc cấu hình mới nếu chưa có."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger

