"""Workflow Presets - Các kịch bản mẫu thông dụng tạo sẵn để người dùng sử dụng ngay."""

from typing import List, Dict, Any
from app.core.workflow_models import WorkflowDefinition, WorkflowStep, RiskLevel


PRESET_WORKFLOWS: List[Dict[str, Any]] = [
    {
        "id": "preset_login_session",
        "name": "🔑 Đăng Nhập & Lưu Phiên (Save Session)",
        "description": "Tự động đăng nhập vào website và lưu cookie/storage_state để các lần chạy sau không cần đăng nhập lại.",
        "workflow": WorkflowDefinition(
            name="Đăng Nhập & Lưu Phiên Tự Động",
            version=1,
            description="Mở trang đăng nhập, điền tài khoản/mật khẩu, nhấp đăng nhập và chụp ảnh lưu bằng chứng.",
            steps=[
                WorkflowStep(
                    id="step_1_open_login",
                    action="navigate",
                    description="Mở trang đăng nhập",
                    risk_level=RiskLevel.LOW,
                    params={"url": "https://example.com/login", "wait_until": "domcontentloaded"},
                ),
                WorkflowStep(
                    id="step_2_fill_username",
                    action="fill",
                    description="Nhập tên đăng nhập hoặc email",
                    risk_level=RiskLevel.MEDIUM,
                    params={"locator": {"placeholder": "Tên đăng nhập hoặc Email"}, "value": "my_username"},
                ),
                WorkflowStep(
                    id="step_3_fill_password",
                    action="fill",
                    description="Nhập mật khẩu",
                    risk_level=RiskLevel.MEDIUM,
                    params={"locator": {"placeholder": "Mật khẩu"}, "value": "my_password"},
                ),
                WorkflowStep(
                    id="step_4_click_submit",
                    action="click",
                    description="Nhấp nút Đăng nhập",
                    risk_level=RiskLevel.MEDIUM,
                    params={"locator": {"role": "button", "name": "Đăng nhập"}},
                ),
                WorkflowStep(
                    id="step_5_wait",
                    action="wait",
                    description="Chờ chuyển hướng vào hệ thống",
                    risk_level=RiskLevel.LOW,
                    params={"seconds": 2.0},
                ),
                WorkflowStep(
                    id="step_6_screenshot",
                    action="screenshot",
                    description="Chụp ảnh màn hình lưu bằng chứng đăng nhập thành công",
                    risk_level=RiskLevel.LOW,
                    params={"filename": "login_success.png"},
                ),
            ],
        ),
    },
    {
        "id": "preset_search_extract",
        "name": "🔍 Tìm Kiếm & Trích Xuất Dữ Liệu (Search & Extract)",
        "description": "Mở trang web, nhập từ khóa tìm kiếm, nhấp tìm và đọc nội dung văn bản hiển thị vào biến.",
        "workflow": WorkflowDefinition(
            name="Tìm Kiếm & Trích Xuất Dữ Liệu",
            version=1,
            description="Tìm kiếm từ khóa và đọc thông tin trả về trên giao diện.",
            steps=[
                WorkflowStep(
                    id="step_1_open_search_page",
                    action="navigate",
                    description="Mở trang tìm kiếm",
                    risk_level=RiskLevel.LOW,
                    params={"url": "https://example.com/search", "wait_until": "domcontentloaded"},
                ),
                WorkflowStep(
                    id="step_2_fill_keyword",
                    action="fill",
                    description="Nhập từ khóa tìm kiếm",
                    risk_level=RiskLevel.MEDIUM,
                    params={"locator": {"placeholder": "Nhập từ khóa tìm kiếm..."}, "value": "thông tin cần tìm"},
                ),
                WorkflowStep(
                    id="step_3_click_search",
                    action="click",
                    description="Nhấp nút Tìm kiếm",
                    risk_level=RiskLevel.MEDIUM,
                    params={"locator": {"role": "button", "name": "Tìm kiếm"}},
                ),
                WorkflowStep(
                    id="step_4_wait_result",
                    action="wait_for",
                    description="Chờ bảng kết quả xuất hiện",
                    risk_level=RiskLevel.LOW,
                    params={"locator": {"css": ".search-results"}, "state": "visible", "timeout_ms": 10000},
                ),
                WorkflowStep(
                    id="step_5_read_result",
                    action="read_text",
                    description="Đọc nội dung kết quả đầu tiên vào biến {{first_result}}",
                    risk_level=RiskLevel.LOW,
                    params={"locator": {"css": ".search-results .item:first-child"}, "output_variable": "first_result"},
                ),
                WorkflowStep(
                    id="step_6_screenshot",
                    action="screenshot",
                    description="Chụp ảnh lưu kết quả tìm kiếm",
                    risk_level=RiskLevel.LOW,
                    params={"filename": "search_result.png"},
                ),
            ],
        ),
    },
    {
        "id": "preset_monitor_screenshot",
        "name": "📸 Giám Sát Trang Web & Chụp Ảnh (Monitor & Capture)",
        "description": "Định kỳ mở trang web, chờ hiển thị và chụp ảnh lưu trữ bằng chứng.",
        "workflow": WorkflowDefinition(
            name="Giám Sát Định Kỳ & Chụp Ảnh",
            version=1,
            description="Mở trang web và chụp ảnh màn hình lưu lại.",
            steps=[
                WorkflowStep(
                    id="step_1_open_site",
                    action="navigate",
                    description="Mở trang web cần giám sát",
                    risk_level=RiskLevel.LOW,
                    params={"url": "https://example.com", "wait_until": "domcontentloaded"},
                ),
                WorkflowStep(
                    id="step_2_wait_content",
                    action="wait",
                    description="Chờ 3 giây để trang hiển thị đầy đủ",
                    risk_level=RiskLevel.LOW,
                    params={"seconds": 3.0},
                ),
                WorkflowStep(
                    id="step_3_screenshot",
                    action="screenshot",
                    description="Chụp ảnh toàn màn hình",
                    risk_level=RiskLevel.LOW,
                    params={"filename": "monitor_snapshot.png"},
                ),
            ],
        ),
    },
    {
        "id": "preset_form_submission",
        "name": "📝 Điền Biểu Mẫu & Gửi Đơn (Form Submission)",
        "description": "Điền biểu mẫu nhiều trường, chụp ảnh trước khi gửi và nhấp gửi đơn có bảo vệ Dry-run.",
        "workflow": WorkflowDefinition(
            name="Điền Biểu Mẫu & Gửi Đơn",
            version=1,
            description="Tự động điền họ tên, thông tin và gửi biểu mẫu an toàn.",
            steps=[
                WorkflowStep(
                    id="step_1_open_form",
                    action="navigate",
                    description="Mở trang biểu mẫu",
                    risk_level=RiskLevel.LOW,
                    params={"url": "https://example.com/register", "wait_until": "domcontentloaded"},
                ),
                WorkflowStep(
                    id="step_2_fill_name",
                    action="fill",
                    description="Điền họ và tên",
                    risk_level=RiskLevel.MEDIUM,
                    params={"locator": {"placeholder": "Họ và tên"}, "value": "Nguyễn Văn A"},
                ),
                WorkflowStep(
                    id="step_3_fill_code",
                    action="fill",
                    description="Điền mã thông tin",
                    risk_level=RiskLevel.MEDIUM,
                    params={"locator": {"placeholder": "Mã đăng ký"}, "value": "REG-2026"},
                ),
                WorkflowStep(
                    id="step_4_before_shot",
                    action="screenshot",
                    description="Chụp ảnh dữ liệu trên biểu mẫu trước khi gửi",
                    risk_level=RiskLevel.LOW,
                    params={"filename": "form_before_submit.png"},
                ),
                WorkflowStep(
                    id="step_5_submit",
                    action="click",
                    description="Gửi biểu mẫu đăng ký (Rủi ro cao)",
                    risk_level=RiskLevel.HIGH,
                    params={"locator": {"role": "button", "name": "Gửi thông tin"}},
                ),
                WorkflowStep(
                    id="step_6_after_shot",
                    action="screenshot",
                    description="Chụp ảnh xác nhận gửi thành công",
                    risk_level=RiskLevel.LOW,
                    params={"filename": "form_after_submit.png"},
                ),
            ],
        ),
    },
]
