"""Recovery Engine - Phân loại lỗi và chính sách phục hồi có kiểm soát.

Tuân thủ Mục 4.5 của tài liệu đặc tả:
- Không reload mù quáng với mọi lỗi.
- Exponential backoff + jitter.
- Tạm dừng và yêu cầu người dùng khi gặp CAPTCHA/MFA hoặc Queue.
- Ngăn chặn lặp lại hành động tác động nghiệp vụ (Idempotency / Duplicate prevention).
"""

import random
import asyncio
import inspect
from enum import Enum
from typing import Optional, Dict, Any, Callable
from app.utils.logging_config import get_logger

logger = get_logger("autoweb.recovery")


class ErrorCategory(str, Enum):
    """Phân loại lỗi theo tài liệu đặc tả."""
    LOCATOR_NOT_FOUND = "locator_not_found"      # Locator chưa xuất hiện
    PAGE_LOAD_TIMEOUT = "page_load_timeout"      # Hết thời gian tải trang
    NETWORK_DISCONNECTED = "network_disconnected"# Mất kết nối mạng
    SERVER_ERROR_5XX = "server_error_5xx"        # HTTP 500, 502, 503, 504
    SESSION_EXPIRED = "session_expired"          # Hết hạn phiên đăng nhập
    CAPTCHA_OR_MFA = "captcha_or_mfa"            # Website yêu cầu xác thực bổ sung
    QUEUE_DETECTED = "queue_detected"            # Đang trong hàng đợi ảo (không được reload)
    ACTION_ALREADY_SUCCEEDED = "already_succeeded" # Action đã thành công trước đó
    UNKNOWN_STATE = "unknown_state"              # Không thể xác định kết quả


class RetryPolicy:
    """Chính sách thử lại với exponential backoff và jitter ngẫu nhiên."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay_seconds: float = 1.0,
        max_delay_seconds: float = 10.0,
        backoff_factor: float = 2.0,
        enable_jitter: bool = True,
    ):
        self.max_retries = max_retries
        self.base_delay_seconds = base_delay_seconds
        self.max_delay_seconds = max_delay_seconds
        self.backoff_factor = backoff_factor
        self.enable_jitter = enable_jitter

    def calculate_delay(self, attempt: int) -> float:
        """Tính toán độ trễ backoff: delay = min(base * (factor ^ attempt), max) + jitter."""
        delay = self.base_delay_seconds * (self.backoff_factor ** attempt)
        delay = min(delay, self.max_delay_seconds)
        if self.enable_jitter:
            jitter = random.uniform(0.1, 0.5) * delay
            delay += jitter
        return delay


class RecoveryEngine:
    """Bộ máy phân loại lỗi và điều phối phục hồi."""

    @staticmethod
    def classify_error(exception: Exception, page_content: Optional[str] = None) -> ErrorCategory:
        """Phân loại nguyên nhân lỗi dựa trên Exception và nội dung DOM."""
        err_str = str(exception).lower()

        # 1. Phát hiện CAPTCHA / MFA
        if page_content and isinstance(page_content, str) and any(term in page_content.lower() for term in ["captcha", "recaptcha", "hcaptcha", "xác thực mfa", "otp"]):
            return ErrorCategory.CAPTCHA_OR_MFA

        # 2. Phát hiện Queue hàng đợi ảo
        if page_content and isinstance(page_content, str) and any(term in page_content.lower() for term in ["vui lòng chờ trong hàng đợi", "you are in line", "waiting room"]):
            return ErrorCategory.QUEUE_DETECTED

        # 3. Hết hạn phiên
        if page_content and isinstance(page_content, str) and any(term in page_content.lower() for term in ["phiên đăng nhập hết hạn", "session expired", "vui lòng đăng nhập lại"]):
            return ErrorCategory.SESSION_EXPIRED

        # 4. Lỗi máy chủ 5xx
        if any(code in err_str for code in ["500", "502", "503", "504", "internal server error", "bad gateway"]):
            return ErrorCategory.SERVER_ERROR_5XX

        # 5. Mất kết nối
        if any(term in err_str for term in ["net::err_internet_disconnected", "connection reset", "connection refused"]):
            return ErrorCategory.NETWORK_DISCONNECTED

        # 6. Timeout / Locator
        if "timeout" in err_str and "waiting for locator" in err_str:
            return ErrorCategory.LOCATOR_NOT_FOUND
        if "timeout" in err_str:
            return ErrorCategory.PAGE_LOAD_TIMEOUT

        return ErrorCategory.UNKNOWN_STATE

    @staticmethod
    def is_retryable(category: ErrorCategory) -> bool:
        """Xác định loại lỗi có được phép thử lại tự động hay không."""
        non_retryable = [
            ErrorCategory.CAPTCHA_OR_MFA,
            ErrorCategory.SESSION_EXPIRED,
            ErrorCategory.QUEUE_DETECTED,
            ErrorCategory.UNKNOWN_STATE,
            ErrorCategory.ACTION_ALREADY_SUCCEEDED,
        ]
        return category not in non_retryable

    async def execute_with_recovery(
        self,
        action_fn: Callable[[], Any],
        policy: Optional[RetryPolicy] = None,
        get_dom_fn: Optional[Callable[[], Any]] = None,
    ) -> Any:
        """Thực thi hàm hành động với cơ chế kiểm soát phục hồi an toàn."""
        pol = policy or RetryPolicy()
        attempt = 0

        while attempt < pol.max_retries:
            try:
                return await action_fn()
            except Exception as e:
                # Trích xuất DOM an toàn dù get_dom_fn là async hay sync
                dom_text = ""
                if get_dom_fn:
                    try:
                        res = get_dom_fn()
                        if inspect.isawaitable(res):
                            dom_text = await res
                        elif isinstance(res, str):
                            dom_text = res
                    except Exception:
                        dom_text = ""

                category = self.classify_error(e, page_content=dom_text)
                
                logger.warning(
                    f"[RECOVERY] Lần thử {attempt + 1}/{pol.max_retries} gặp lỗi: {e} -> Phân loại: {category.value}"
                )

                if not self.is_retryable(category):
                    logger.error(
                        f"[RECOVERY] Lỗi '{category.value}' không được phép thử lại tự động. Yêu cầu người dùng can thiệp."
                    )
                    raise

                attempt += 1
                if attempt >= pol.max_retries:
                    logger.error(f"[RECOVERY] Đã đạt giới hạn số lần thử lại ({pol.max_retries}). Dừng tác vụ.")
                    raise

                delay = pol.calculate_delay(attempt)
                logger.info(f"[RECOVERY] Chờ {delay:.2f}s trước khi thử lại lần {attempt + 1}...")
                await asyncio.sleep(delay)
