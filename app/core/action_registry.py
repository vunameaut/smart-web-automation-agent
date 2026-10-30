"""Action Registry - Quản lý và đăng ký các action có thể thực thi trong Workflow."""

from typing import Dict, Type, Optional
from app.actions.base import BaseAction
from app.actions.standard_actions import (
    NavigateAction,
    ClickAction,
    FillAction,
    WaitForAction,
    ReadTextAction,
    ScreenshotAction,
    WaitAction,
)


class ActionRegistry:
    """Kho lưu trữ và khởi tạo các Action theo tên."""

    def __init__(self):
        self._actions: Dict[str, BaseAction] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Đăng ký các action chuẩn của hệ thống."""
        self.register("navigate", NavigateAction())
        self.register("click", ClickAction())
        self.register("fill", FillAction())
        self.register("wait_for", WaitForAction())
        self.register("read_text", ReadTextAction())
        self.register("screenshot", ScreenshotAction())
        self.register("wait", WaitAction())

    def register(self, name: str, action: BaseAction) -> None:
        """Đăng ký một action mới."""
        self._actions[name.lower()] = action

    def get(self, name: str) -> Optional[BaseAction]:
        """Lấy action theo tên."""
        return self._actions.get(name.lower())

    def has(self, name: str) -> bool:
        """Kiểm tra xem action có tồn tại hay không."""
        return name.lower() in self._actions


# Singleton registry mặc định
_default_registry: Optional[ActionRegistry] = None


def get_action_registry() -> ActionRegistry:
    global _default_registry
    if _default_registry is None:
        _default_registry = ActionRegistry()
    return _default_registry

