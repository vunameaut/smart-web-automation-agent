"""Demo Phase 1: Browser Automation Foundation.

Kịch bản demo tự động hóa:
1. Khởi chạy Chromium (Headful, có thể quan sát trực tiếp trên màn hình Windows).
2. Điều hướng đến trang web thử nghiệm (test_page.html).
3. Nhập dữ liệu an toàn vào các ô Tên và Mã học phần theo các tiêu chí locator ưu tiên (Label, Placeholder).
4. Click nút 'Xác nhận đăng ký' theo Role và Name.
5. Xác minh kết quả nghiệp vụ từ DOM.
6. Chụp ảnh màn hình lưu vào artifacts/screenshots/.
7. Thử nghiệm cơ chế an toàn: Từ chối click nút bị khóa (disabled).
8. Đóng trình duyệt an toàn và báo cáo kết quả.
"""

import sys
import io

# Đảm bảo mã hóa UTF-8 trên Windows console
if sys.platform == "win32":
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import asyncio
from pathlib import Path
from app.browser import BrowserController, LocatorConfig
from app.utils.logging_config import get_logger

logger = get_logger("demo_phase1")


async def run_demo():
    print("=" * 70)
    print("   SMART WEB AUTOMATION AGENT - PHASE 1 FOUNDATION DEMO")
    print("=" * 70)

    # Đường dẫn trang web test cục bộ
    test_html_file = Path(__file__).parent / "tests" / "fixtures" / "test_page.html"
    test_url = test_html_file.as_uri()

    print(f"\n[1] Chuẩn bị khởi chạy Chromium với URL: {test_url}")
    
    # Khởi tạo BrowserController: headless=False để người dùng nhìn thấy thao tác thực tế
    async with BrowserController(headless=False, slow_mo_ms=600) as browser:
        # 1. Điều hướng
        print("\n[2] Điều hướng tới trang thử nghiệm...")
        success = await browser.navigate(test_url)
        if not success:
            print("[-] Điều hướng thất bại!")
            return

        # 2. Nhập họ tên
        print("\n[3] Nhập họ tên học viên vào ô có label 'Tên người dùng:'...")
        await browser.fill(
            LocatorConfig(label="Tên người dùng:"),
            value="Nguyễn Văn A"
        )

        # 3. Nhập mã môn học
        print("\n[4] Nhập mã học phần vào ô có placeholder 'Ví dụ: CS101'...")
        await browser.fill(
            LocatorConfig(placeholder="Ví dụ: CS101"),
            value="CS101-WEB-AUTOMATION"
        )

        # 4. Chụp ảnh màn hình trước khi xác nhận
        print("\n[5] Chụp ảnh màn hình trước khi submit...")
        before_shot = await browser.take_screenshot("demo_before_submit")
        print(f"    -> Đã lưu ảnh: {before_shot.name if before_shot else 'N/A'}")

        # 5. Click xác nhận
        print("\n[6] Click nút [Xác nhận đăng ký] theo role='button' và name='Xác nhận đăng ký'...")
        click_success = await browser.click(
            LocatorConfig(role="button", name="Xác nhận đăng ký")
        )

        if click_success:
            # 6. Xác minh kết quả nghiệp vụ
            print("\n[7] Xác minh phản hồi từ hệ thống web...")
            result_text = await browser.get_text(LocatorConfig(role="status"))
            print(f"    [DOM Verification] Nội dung hiển thị: \"{result_text}\"")

            if result_text and "Nguyễn Văn A" in result_text:
                print("    [+] XÁC MINH NGHIỆP VỤ THÀNH CÔNG: Dữ liệu đã được ghi nhận chính xác!")
            else:
                print("    [-] CẢNH BÁO: Kết quả hiển thị không khớp dữ liệu mong đợi.")

        # 7. Chụp ảnh màn hình kết quả sau khi đăng ký
        print("\n[8] Chụp ảnh màn hình kết quả thành công...")
        after_shot = await browser.take_screenshot("demo_after_submit")
        print(f"    -> Đã lưu ảnh: {after_shot.name if after_shot else 'N/A'}")

        # 8. Kiểm thử quy tắc 'Không click mù quáng' với nút Disabled
        print("\n[9] Kiểm thử cơ chế bảo vệ: Thử click nút đang bị khóa (Disabled)...")
        disabled_click = await browser.click(
            LocatorConfig(role="button", name="Nút bị khóa"),
            timeout_ms=1500
        )
        if not disabled_click:
            print("    [+] Đúng như thiết kế: Hệ thống từ chối click nút Disabled để bảo vệ phiên!")

        print("\n[10] Chuẩn bị đóng browser an toàn sau 2 giây...")
        await asyncio.sleep(2)

    print("\n" + "=" * 70)
    print("   DEMO PHASE 1 HOÀN TẤT THÀNH CÔNG RỰC RỠ!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_demo())
