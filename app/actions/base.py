"""Base Action và Action Context cho Workflow Engine."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
from app.browser.browser_controller import BrowserController
from app.utils.logging_config import get_logger

logger = get_logger("autoweb.actions")


class DomainSecurityViolation(Exception):
    """Lỗi khi truy cập ngoài danh sách target_domains cho phép."""
    pass


class ActionContext:
    """Ngữ cảnh truyền vào mỗi Action khi thực thi."""

    def __init__(
        self,
        browser: BrowserController,
        variables: Optional[Dict[str, Any]] = None,
        dry_run: bool = False,
        target_domains: Optional[List[str]] = None,
    ):
        self.browser = browser
        self.variables: Dict[str, Any] = variables or {}
        self.dry_run = dry_run
        self.target_domains = target_domains or []
        self.logger = logger

    def validate_domain(self, url: str) -> None:
        """Kiểm tra xem URL có thuộc target_domains được phép thao tác hay không."""
        if not self.target_domains:
            return  # Không cấu hình ràng buộc

        parsed = urlparse(url)
        # Bỏ qua scheme cục bộ như file://
        if parsed.scheme == "file":
            return

        hostname = parsed.hostname or ""
        is_allowed = any(
            hostname == domain or hostname.endswith("." + domain)
            for domain in self.target_domains
        )
        if not is_allowed:
            raise DomainSecurityViolation(
                f"Vi phạm chính sách bảo mật: Domain '{hostname}' không nằm trong danh sách được phép: {self.target_domains}"
            )

    def resolve_template(self, text: str) -> str:
        """Thay thế các biến dạng {{var_name}} bằng giá trị trong context."""
        if not isinstance(text, str):
            return text
        result = text
        for key, val in self.variables.items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in result:
                result = result.replace(placeholder, str(val))
        return result


class BaseAction(ABC):
    """Lớp cơ sở trừu tượng cho tất cả các Action trong hệ thống."""

    @abstractmethod
    async def execute(self, context: ActionContext, params: Dict[str, Any]) -> Any:
        """Thực thi action với tham số và ngữ cảnh được cung cấp."""
        pass
