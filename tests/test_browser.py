"""Tests for BrowserController and LocatorHelper - Phase 1."""

import pytest
from pathlib import Path
from app.browser import BrowserController, LocatorConfig
from app.config import get_settings


@pytest.fixture
def test_page_url() -> str:
    """Trả về file:// URI trỏ tới trang HTML kiểm thử local."""
    html_path = Path(__file__).parent / "fixtures" / "test_page.html"
    return html_path.as_uri()


@pytest.mark.asyncio
async def test_browser_lifecycle():
    """Kiểm tra khởi động và đóng browser an toàn."""
    controller = BrowserController(headless=True)
    assert not controller.is_running

    await controller.start()
    assert controller.is_running
    assert controller.page is not None

    await controller.stop()
    assert not controller.is_running


@pytest.mark.asyncio
async def test_navigation_and_interactions(test_page_url: str):
    """Kiểm tra điều hướng, nhập liệu, click và xác minh kết quả nghiệp vụ."""
    async with BrowserController(headless=True) as browser:
        # 1. Điều hướng
        nav_success = await browser.navigate(test_page_url)
        assert nav_success is True

        # 2. Nhập liệu qua Label
        fill_name = await browser.fill(
            LocatorConfig(label="Tên người dùng:"),
            value="Nguyễn Văn A"
        )
        assert fill_name is True

        # 3. Nhập liệu qua Placeholder
        fill_code = await browser.fill(
            LocatorConfig(placeholder="Ví dụ: CS101"),
            value="CS101"
        )
        assert fill_code is True

        # 4. Click qua Role và Name
        click_success = await browser.click(
            LocatorConfig(role="button", name="Xác nhận đăng ký")
        )
        assert click_success is True

        # 5. Xác minh kết quả nghiệp vụ bằng nội dung hiển thị
        result_text = await browser.get_text(LocatorConfig(role="status"))
        assert result_text is not None
        assert "Đăng ký thành công cho: Nguyễn Văn A (CS101)" in result_text

        # 6. Chụp ảnh màn hình và kiểm tra file tồn tại
        screenshot_path = await browser.take_screenshot("test_success")
        assert screenshot_path is not None
        assert screenshot_path.exists()
        assert screenshot_path.stat().st_size > 0


@pytest.mark.asyncio
async def test_disabled_element_protection(test_page_url: str):
    """Tuân thủ 'Không click mù quáng': Không click vào phần tử bị disabled."""
    async with BrowserController(headless=True) as browser:
        await browser.navigate(test_page_url)
        # Nút bị khóa (disabled)
        click_res = await browser.click(
            LocatorConfig(role="button", name="Nút bị khóa"),
            timeout_ms=1000
        )
        assert click_res is False


@pytest.mark.asyncio
async def test_timeout_handling(test_page_url: str):
    """Kiểm tra cơ chế xử lý timeout an toàn, không làm crash ứng dụng."""
    async with BrowserController(headless=True) as browser:
        await browser.navigate(test_page_url)
        # Thử click vào một nút không hề tồn tại với timeout ngắn
        click_res = await browser.click(
            LocatorConfig(role="button", name="Nút Không Tồn Tại"),
            timeout_ms=500
        )
        assert click_res is False

