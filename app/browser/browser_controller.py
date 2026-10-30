"""Browser Controller module - Quản lý Chromium và tương tác trình duyệt an toàn."""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Union
from playwright.async_api import (
    async_playwright,
    Playwright,
    Browser,
    BrowserContext,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    Error as PlaywrightError
)

from app.config import get_settings
from app.utils.logging_config import get_logger
from app.browser.locator_helper import resolve_locator, LocatorConfig

logger = get_logger("autoweb.browser")


class BrowserController:
    """Quản lý vòng đời và các thao tác tự động hóa với Playwright Chromium."""

    def __init__(
        self,
        headless: Optional[bool] = None,
        slow_mo_ms: Optional[int] = None,
        timeout_ms: Optional[int] = None,
        storage_state_path: Optional[str] = None,
    ):
        self.settings = get_settings()
        # Đọc cấu hình mặc định từ settings.HEADLESS nếu không truyền tham số
        self.headless = headless if headless is not None else self.settings.HEADLESS
        self.slow_mo_ms = slow_mo_ms if slow_mo_ms is not None else self.settings.SLOW_MO_MS
        self.default_timeout_ms = timeout_ms if timeout_ms is not None else self.settings.DEFAULT_TIMEOUT_MS
        self.storage_state_path = storage_state_path

        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    @property
    def is_running(self) -> bool:
        """Kiểm tra xem browser và context có đang mở hay không."""
        return self._browser is not None and self._browser.is_connected() and self._page is not None

    @property
    def page(self) -> Page:
        """Truy cập trang hiện tại."""
        if not self._page or self._page.is_closed():
            raise RuntimeError("Trang chưa được khởi tạo hoặc đã bị đóng. Hãy gọi start() trước.")
        return self._page

    async def start(self) -> Page:
        """Khởi động Playwright, Chromium, Context (hỗ trợ storage_state session) và Page."""
        if self.is_running:
            logger.info("Browser đã đang chạy.")
            return self.page

        logger.info(
            f"Đang khởi chạy Chromium (headless={self.headless}, slow_mo={self.slow_mo_ms}ms, timeout={self.default_timeout_ms}ms)..."
        )
        try:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless,
                slow_mo=self.slow_mo_ms,
            )

            # Cấu hình context kèm storage_state nếu file tồn tại
            context_args: Dict[str, Any] = {
                "viewport": {
                    "width": self.settings.VIEWPORT_WIDTH,
                    "height": self.settings.VIEWPORT_HEIGHT,
                },
                "ignore_https_errors": False,
            }

            if self.storage_state_path and Path(self.storage_state_path).exists():
                logger.info(f"Khôi phục phiên đăng nhập từ file: {self.storage_state_path}")
                context_args["storage_state"] = self.storage_state_path

            self._context = await self._browser.new_context(**context_args)
            self._context.set_default_timeout(self.default_timeout_ms)
            self._page = await self._context.new_page()
            
            logger.info("Khởi động Chromium thành công.")
            return self._page
        except Exception as e:
            logger.error(f"Khởi động Chromium thất bại: {e}")
            await self.stop()
            raise

    async def save_storage_state(self, path: Optional[str] = None) -> Optional[str]:
        """Lưu lại cookies và local storage của phiên đăng nhập hiện tại."""
        if not self._context:
            return None
        target_path = path or self.storage_state_path
        if not target_path:
            # Tạo đường dẫn mặc định
            target_path = str(self.settings.PROFILES_DIR / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

        Path(target_path).parent.mkdir(parents=True, exist_ok=True)
        await self._context.storage_state(path=target_path)
        logger.info(f"Đã lưu session state vào: {target_path}")
        return target_path

    async def stop(self) -> None:
        """Đóng an toàn toàn bộ tài nguyên browser, context và tiến trình Playwright."""
        logger.info("Đang đóng các tài nguyên trình duyệt...")
        
        # Lưu lại session state nếu có đường dẫn
        if self._context and self.storage_state_path:
            try:
                await self.save_storage_state(self.storage_state_path)
            except Exception as e:
                logger.warning(f"Không thể tự động lưu session state trước khi đóng: {e}")

        if self._page and not self._page.is_closed():
            try:
                await self._page.close()
            except Exception as e:
                logger.warning(f"Lỗi khi đóng Page: {e}")
            self._page = None

        if self._context:
            try:
                await self._context.close()
            except Exception as e:
                logger.warning(f"Lỗi khi đóng Context: {e}")
            self._context = None

        if self._browser:
            try:
                await self._browser.close()
            except Exception as e:
                logger.warning(f"Lỗi khi đóng Browser: {e}")
            self._browser = None

        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception as e:
                logger.warning(f"Lỗi khi dừng Playwright engine: {e}")
            self._playwright = None

        logger.info("Đã đóng toàn bộ tài nguyên trình duyệt an toàn.")

    async def navigate(
        self,
        url: str,
        wait_until: str = "domcontentloaded",
        timeout_ms: Optional[int] = None,
    ) -> bool:
        """Điều hướng an toàn đến URL được chỉ định."""
        effective_timeout = timeout_ms or self.settings.NAVIGATION_TIMEOUT_MS
        logger.info(f"Đang điều hướng tới: {url} (wait_until={wait_until}, timeout={effective_timeout}ms)")
        try:
            response = await self.page.goto(url, wait_until=wait_until, timeout=effective_timeout)
            status_code = response.status if response else "Unknown"
            logger.info(f"Điều hướng thành công tới {url} (HTTP Status: {status_code})")
            return True
        except PlaywrightTimeoutError:
            logger.error(f"Hết thời gian chờ (Timeout {effective_timeout}ms) khi truy cập: {url}")
            await self.take_screenshot(name_prefix="timeout_navigate")
            return False
        except Exception as e:
            logger.error(f"Lỗi khi điều hướng tới {url}: {e}")
            await self.take_screenshot(name_prefix="error_navigate")
            return False

    async def click(
        self,
        locator_target: Union[LocatorConfig, Dict[str, Any], str],
        timeout_ms: Optional[int] = None,
        force: bool = False,
    ) -> bool:
        """Thực hiện click an toàn: kiểm tra visible và enabled trước khi click."""
        effective_timeout = timeout_ms or self.default_timeout_ms
        loc = resolve_locator(self.page, locator_target)
        desc = locator_target if isinstance(locator_target, str) else (
            locator_target.describe() if isinstance(locator_target, LocatorConfig) else str(locator_target)
        )
        logger.info(f"Đang chuẩn bị click vào phần tử: [{desc}]")

        try:
            await loc.wait_for(state="visible", timeout=effective_timeout)
            if not force and not await loc.is_enabled():
                logger.warning(f"Phần tử [{desc}] đang ở trạng thái Disabled, không thể click an toàn.")
                return False

            await loc.click(timeout=effective_timeout, force=force)
            logger.info(f"Click thành công vào phần tử: [{desc}]")
            return True
        except PlaywrightTimeoutError:
            logger.error(f"Timeout khi chờ click vào phần tử: [{desc}]")
            await self.take_screenshot(name_prefix="timeout_click")
            return False
        except Exception as e:
            logger.error(f"Lỗi khi click vào phần tử [{desc}]: {e}")
            await self.take_screenshot(name_prefix="error_click")
            return False

    async def fill(
        self,
        locator_target: Union[LocatorConfig, Dict[str, Any], str],
        value: str,
        timeout_ms: Optional[int] = None,
        is_sensitive: bool = False,
    ) -> bool:
        """Nhập liệu an toàn vào trường nhập dữ liệu."""
        effective_timeout = timeout_ms or self.default_timeout_ms
        loc = resolve_locator(self.page, locator_target)
        desc = locator_target if isinstance(locator_target, str) else (
            locator_target.describe() if isinstance(locator_target, LocatorConfig) else str(locator_target)
        )
        display_val = "[PROTECTED]" if is_sensitive else value
        logger.info(f"Đang nhập giá trị '{display_val}' vào ô: [{desc}]")

        try:
            await loc.wait_for(state="visible", timeout=effective_timeout)
            await loc.fill(value, timeout=effective_timeout)
            logger.info(f"Nhập liệu thành công vào: [{desc}]")
            return True
        except PlaywrightTimeoutError:
            logger.error(f"Timeout khi chờ nhập liệu vào: [{desc}]")
            await self.take_screenshot(name_prefix="timeout_fill")
            return False
        except Exception as e:
            logger.error(f"Lỗi khi nhập liệu vào [{desc}]: {e}")
            await self.take_screenshot(name_prefix="error_fill")
            return False

    async def get_text(
        self,
        locator_target: Union[LocatorConfig, Dict[str, Any], str],
        timeout_ms: Optional[int] = None,
    ) -> Optional[str]:
        """Đọc văn bản của phần tử."""
        effective_timeout = timeout_ms or self.default_timeout_ms
        loc = resolve_locator(self.page, locator_target)
        try:
            await loc.wait_for(state="visible", timeout=effective_timeout)
            text = await loc.inner_text(timeout=effective_timeout)
            return text.strip()
        except Exception as e:
            logger.warning(f"Không thể đọc text từ phần tử: {e}")
            return None

    async def take_screenshot(self, name_prefix: str = "screenshot") -> Optional[Path]:
        """Chụp ảnh màn hình trang hiện tại và lưu vào artifacts/screenshots/."""
        if not self._page or self._page.is_closed():
            logger.warning("Không thể chụp ảnh vì page không khả dụng.")
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19]
        filename = f"{name_prefix}_{timestamp}.png"
        filepath = self.settings.SCREENSHOTS_DIR / filename

        try:
            await self.page.screenshot(path=str(filepath), full_page=False)
            logger.info(f"Đã lưu ảnh chụp màn hình tại: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Chụp ảnh màn hình thất bại: {e}")
            return None

    async def __aenter__(self) -> "BrowserController":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.stop()
