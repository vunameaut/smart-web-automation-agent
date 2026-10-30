"""Locator Helper module - Hiện thực hóa quy tắc không click mù quáng.

Ưu tiên định vị phần tử:
1. Role + accessible name
2. Label
3. Placeholder
4. Text
5. Test ID
6. CSS selector
"""

from typing import Optional, Dict, Any, Union
from playwright.async_api import Page, Locator
from app.utils.logging_config import get_logger

logger = get_logger("autoweb.locator")


class LocatorConfig:
    """Định nghĩa cấu hình tìm kiếm phần tử."""
    def __init__(
        self,
        role: Optional[str] = None,
        name: Optional[str] = None,
        label: Optional[str] = None,
        placeholder: Optional[str] = None,
        text: Optional[str] = None,
        test_id: Optional[str] = None,
        css: Optional[str] = None,
        exact: bool = False,
    ):
        self.role = role
        self.name = name
        self.label = label
        self.placeholder = placeholder
        self.text = text
        self.test_id = test_id
        self.css = css
        self.exact = exact

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LocatorConfig":
        return cls(
            role=data.get("role"),
            name=data.get("name"),
            label=data.get("label"),
            placeholder=data.get("placeholder"),
            text=data.get("text"),
            test_id=data.get("test_id"),
            css=data.get("css"),
            exact=data.get("exact", False),
        )

    def describe(self) -> str:
        """Mô tả ngắn gọn tiêu chí locator phục vụ ghi log."""
        parts = []
        if self.role:
            parts.append(f"role='{self.role}'(name='{self.name}')" if self.name else f"role='{self.role}'")
        if self.label:
            parts.append(f"label='{self.label}'")
        if self.placeholder:
            parts.append(f"placeholder='{self.placeholder}'")
        if self.text:
            parts.append(f"text='{self.text}'")
        if self.test_id:
            parts.append(f"test_id='{self.test_id}'")
        if self.css:
            parts.append(f"css='{self.css}'")
        return ", ".join(parts) or "unknown locator"


def resolve_locator(page: Page, config: Union[LocatorConfig, Dict[str, Any], str]) -> Locator:
    """Phân giải cấu hình locator theo thứ tự ưu tiên được chỉ định trong tài liệu đặc tả.
    
    Thứ tự ưu tiên:
    1. role (+ name)
    2. label
    3. placeholder
    4. text
    5. test_id
    6. css
    """
    if isinstance(config, str):
        # Mặc định chuỗi đơn giản được coi là CSS selector
        return page.locator(config)

    if isinstance(config, dict):
        cfg = LocatorConfig.from_dict(config)
    else:
        cfg = config

    # 1. Role (ưu tiên cao nhất - chuẩn accessibility)
    if cfg.role:
        kwargs: Dict[str, Any] = {"exact": cfg.exact}
        if cfg.name is not None:
            kwargs["name"] = cfg.name
        return page.get_by_role(cfg.role, **kwargs)

    # 2. Label
    if cfg.label:
        return page.get_by_label(cfg.label, exact=cfg.exact)

    # 3. Placeholder
    if cfg.placeholder:
        return page.get_by_placeholder(cfg.placeholder, exact=cfg.exact)

    # 4. Text
    if cfg.text:
        return page.get_by_text(cfg.text, exact=cfg.exact)

    # 5. Test ID
    if cfg.test_id:
        return page.get_by_test_id(cfg.test_id)

    # 6. CSS selector
    if cfg.css:
        return page.locator(cfg.css)

    raise ValueError(f"Không có tiêu chí locator hợp lệ nào được cung cấp: {cfg.describe()}")

