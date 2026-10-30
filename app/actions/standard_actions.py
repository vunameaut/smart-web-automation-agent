"""Các Action cơ bản phục vụ Workflow Engine."""

import asyncio
from typing import Dict, Any
from app.actions.base import BaseAction, ActionContext
from app.browser.locator_helper import resolve_locator, LocatorConfig


class NavigateAction(BaseAction):
    """Mở URL mục tiêu."""

    async def execute(self, context: ActionContext, params: Dict[str, Any]) -> bool:
        raw_url = params.get("url")
        if not raw_url:
            raise ValueError("Action 'navigate' yêu cầu tham số 'url'.")
        
        url = context.resolve_template(raw_url)
        wait_until = params.get("wait_until", "domcontentloaded")
        timeout_ms = params.get("timeout_ms")
        
        success = await context.browser.navigate(url, wait_until=wait_until, timeout_ms=timeout_ms)
        if not success:
            raise RuntimeError(f"Không thể điều hướng tới URL: {url}")
        return True


class ClickAction(BaseAction):
    """Click an toàn vào phần tử."""

    async def execute(self, context: ActionContext, params: Dict[str, Any]) -> bool:
        locator = params.get("locator")
        if not locator:
            raise ValueError("Action 'click' yêu cầu tham số 'locator'.")
        
        force = params.get("force", False)
        timeout_ms = params.get("timeout_ms")
        
        if context.dry_run:
            context.logger.info(f"[DRY-RUN] Bỏ qua thao tác click thực tế vào [{locator}].")
            return True

        success = await context.browser.click(locator, timeout_ms=timeout_ms, force=force)
        if not success:
            raise RuntimeError(f"Click thất bại vào phần tử: {locator}")
        return True


class FillAction(BaseAction):
    """Nhập dữ liệu an toàn vào trường nhập."""

    async def execute(self, context: ActionContext, params: Dict[str, Any]) -> bool:
        locator = params.get("locator")
        if not locator:
            raise ValueError("Action 'fill' yêu cầu tham số 'locator'.")
        
        raw_value = str(params.get("value", ""))
        value = context.resolve_template(raw_value)
        is_sensitive = params.get("is_sensitive", False)
        timeout_ms = params.get("timeout_ms")

        success = await context.browser.fill(
            locator,
            value=value,
            timeout_ms=timeout_ms,
            is_sensitive=is_sensitive,
        )
        if not success:
            raise RuntimeError(f"Nhập liệu thất bại vào phần tử: {locator}")
        return True


class WaitForAction(BaseAction):
    """Chờ phần tử đạt trạng thái mong muốn (visible, hidden, attached)."""

    async def execute(self, context: ActionContext, params: Dict[str, Any]) -> bool:
        locator = params.get("locator")
        if not locator:
            raise ValueError("Action 'wait_for' yêu cầu tham số 'locator'.")
        
        state = params.get("state", "visible")
        timeout_ms = params.get("timeout_ms", context.browser.default_timeout_ms)
        
        loc = resolve_locator(context.browser.page, locator)
        await loc.wait_for(state=state, timeout=timeout_ms)
        return True


class ReadTextAction(BaseAction):
    """Đọc văn bản từ phần tử và lưu vào biến context."""

    async def execute(self, context: ActionContext, params: Dict[str, Any]) -> str:
        locator = params.get("locator")
        if not locator:
            raise ValueError("Action 'read_text' yêu cầu tham số 'locator'.")
        
        timeout_ms = params.get("timeout_ms")
        save_to = params.get("save_to")
        
        text = await context.browser.get_text(locator, timeout_ms=timeout_ms)
        if text is None:
            raise RuntimeError(f"Không thể đọc văn bản từ phần tử: {locator}")
        
        if save_to:
            context.variables[save_to] = text
            context.logger.info(f"Đã lưu giá trị đọc được vào biến '{{{{{save_to}}}}}': '{text}'")
            
        return text


class ScreenshotAction(BaseAction):
    """Chụp ảnh màn hình."""

    async def execute(self, context: ActionContext, params: Dict[str, Any]) -> str:
        name_prefix = params.get("name_prefix", "workflow_screenshot")
        filepath = await context.browser.take_screenshot(name_prefix=name_prefix)
        if not filepath:
            raise RuntimeError("Chụp ảnh màn hình thất bại.")
        return str(filepath)


class WaitAction(BaseAction):
    """Dừng tiến trình trong một khoảng thời gian xác định."""

    async def execute(self, context: ActionContext, params: Dict[str, Any]) -> bool:
        seconds = params.get("seconds", 1.0)
        context.logger.info(f"Chờ đợi trong {seconds} giây...")
        await asyncio.sleep(seconds)
        return True

