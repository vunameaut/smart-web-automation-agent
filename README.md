# Smart Web Automation Agent

Hệ thống tự động hóa trình duyệt đáng tin cậy, cục bộ (**Local-first**) trên nền tảng **Windows 11** và **Python 3.12+**, xây dựng bằng **Playwright**, **SQLAlchemy (SQLite)**, **APScheduler**, và giao diện **PySide6**.

Tuân thủ tuyệt đối tài liệu đặc tả [SMART_WEB_AUTOMATION_AGENT_PROJECT_SPEC.md](SMART_WEB_AUTOMATION_AGENT_PROJECT_SPEC.md).

---

## 🌟 Tính năng nổi bật đã hoàn thành

1. **Local-first & Bảo mật:**
   - Hoàn toàn độc lập, lưu trữ dữ liệu tại máy cá nhân với SQLite (`data/autoweb.db`).
   - Tự động làm mờ (redact) mật khẩu, token, secret trong file log `logs/agent.log`.
   - Không yêu cầu Cloud hay API AI bên ngoài cho các luồng nghiệp vụ chuẩn.

2. **Quy tắc cốt lõi: "Không click mù quáng":**
   - Bộ phân giải Locator ưu tiên chuẩn Accessibility: `Role` > `Label` > `Placeholder` > `Text` > `Test ID` > `CSS`.
   - Kiểm tra điều kiện khả dụng (`visible`, `enabled`) trước khi click. Từ chối click nút `Disabled` để bảo vệ phiên làm việc.
   - Luôn xác minh kết quả nghiệp vụ từ DOM sau khi thực hiện hành động.

3. **Workflow Engine & Action Registry:**
   - Định nghĩa kịch bản bằng file YAML/JSON (`workflows/course_registration.yaml`).
   - Đầy đủ các Action cơ bản: `navigate`, `click`, `fill`, `wait_for`, `read_text`, `screenshot`, `wait`.
   - Hỗ trợ cơ chế **Dry Run** (chạy thử an toàn: tự động dừng/bỏ qua các bước High/Critical Risk như đặt hàng, submit form cuối cùng).

4. **Recovery Engine & Scheduler:**
   - Phân loại lỗi thông minh: `CAPTCHA_OR_MFA`, `QUEUE_DETECTED`, `SESSION_EXPIRED`, `SERVER_ERROR_5XX`, `LOCATOR_NOT_FOUND`.
   - Exponential backoff + ngẫu nhiên Jitter.
   - Cơ chế bảo vệ: Không retry vô hạn, không tự động thử lại khi gặp CAPTCHA hoặc hết hạn phiên (yêu cầu người dùng can thiệp).
   - Hỗ trợ tính năng **Pre-warming**: Khởi động trước trình duyệt và điều hướng sớm để chuẩn bị giờ cao điểm.

5. **Giao diện Desktop hiện đại (PySide6):**
   - **Dashboard**: Thống kê số lượng nhiệm vụ, trạng thái chạy và lịch sử gần nhất.
   - **Task Manager**: Danh sách nhiệm vụ, chức năng chạy ngay hoặc chạy thử an toàn (Dry Run).
   - **Live Monitor & Logs**: Giám sát nhật ký thời gian thực từ `logs/agent.log`.
   - **Settings**: Xem cấu hình hệ thống, đường dẫn dữ liệu và trình duyệt.

---

## 📁 Cấu trúc dự án hoàn chỉnh

```text
autoweb/
│
├── app/
│   ├── __init__.py
│   ├── actions/                    # Action Engine & Implementation
│   │   ├── __init__.py
│   │   ├── base.py                 # BaseAction & ActionContext (biến template)
│   │   └── standard_actions.py     # Navigate, Click, Fill, ReadText, Screenshot...
│   │
│   ├── browser/                    # Browser Controller & Locator
│   │   ├── __init__.py
│   │   ├── browser_controller.py   # Quản lý Chromium, viewport, context an toàn
│   │   └── locator_helper.py       # Phân giải theo Role > Label > Text
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py             # Cấu hình đường dẫn, timeout, headless mode
│   │
│   ├── core/                       # Core Engines
│   │   ├── __init__.py
│   │   ├── action_registry.py      # Đăng ký và quản lý Action
│   │   ├── workflow_models.py      # Pydantic schema cho Workflow & Step
│   │   ├── workflow_engine.py      # Điều phối thực thi và xác minh điều kiện
│   │   ├── recovery_engine.py      # Phân loại lỗi, retry policy, backoff + jitter
│   │   ├── scheduler.py            # APScheduler & Pre-warming browser
│   │   └── task_manager.py         # Quản lý CRUD nhiệm vụ
│   │
│   ├── database/                   # SQLite Persistence
│   │   ├── __init__.py
│   │   ├── database.py             # SQLAlchemy Engine & Session
│   │   ├── models.py               # Bảng tasks, workflows, executions, step_executions, artifacts
│   │   └── repository.py           # Repository truy cập dữ liệu
│   │
│   ├── ui/                         # Desktop UI
│   │   ├── __init__.py
│   │   └── main_window.py          # PySide6 MainWindow (Dashboard, Task, Logs)
│   │
│   └── utils/
│       ├── __init__.py
│       └── logging_config.py       # Logging UTF-8, che giấu dữ liệu nhạy cảm
│
├── workflows/
│   └── course_registration.yaml    # File mẫu kịch bản đăng ký học phần
│
├── tests/
│   ├── fixtures/
│   │   └── test_page.html          # Trang web thử nghiệm mô phỏng cục bộ
│   ├── test_browser.py             # Test Browser Controller & Timeout
│   ├── test_workflow_engine.py     # Test Workflow Engine, YAML, Dry-run
│   └── test_scheduler_and_db.py    # Test SQLite CRUD, Scheduler, Recovery Engine
│
├── artifacts/
│   └── screenshots/                # Thư mục lưu ảnh chụp màn hình khi chạy/lỗi
├── data/
│   └── autoweb.db                  # Database SQLite cục bộ
├── logs/
│   └── agent.log                   # File log có cấu trúc
│
├── main.py                         # Điểm vào chính của ứng dụng (UI / CLI)
├── demo_phase1.py                  # Script demo thực tế mở trình duyệt trực quan
├── requirements.txt                # Danh mục thư viện phụ thuộc
├── pyproject.toml                  # Cấu hình dự án & Pytest
├── .gitignore                      # Bộ lọc git an toàn
└── README.md                       # Hướng dẫn chi tiết
```

---

## 🚀 Hướng dẫn cài đặt và sử dụng

### 1. Chuẩn bị môi trường (Windows 11 / PowerShell)

```powershell
cd "D:\hoc tap\tools\autoweb"

# Cho phép chạy script trong session PowerShell hiện tại
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -Force

# Tạo và kích hoạt môi trường ảo
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Cài đặt toàn bộ thư viện cần thiết
pip install -r requirements.txt

# Cài đặt Chromium cho Playwright
playwright install chromium
```

### 2. Khởi chạy ứng dụng Desktop UI (PySide6)

Để mở giao diện điều khiển Desktop hiện đại:
```powershell
python main.py
```

### 3. Chạy qua Command Line (CLI)

- Xem các tham số trợ giúp:
  ```powershell
  python main.py --help
  ```
- Chạy kịch bản Demo mở trình duyệt:
  ```powershell
  python main.py --demo
  ```

### 4. Chạy toàn bộ Test tự động (Pytest)

Chạy tất cả 12 bài kiểm thử tự động bao quát toàn bộ các tầng kiến trúc:
```powershell
pytest tests/ -v
```

---

## 📋 Kết quả kiểm thử tự động (12/12 Tests Passed)

```text
tests/test_browser.py::test_browser_lifecycle PASSED                     [  8%]
tests/test_browser.py::test_navigation_and_interactions PASSED           [ 16%]
tests/test_browser.py::test_disabled_element_protection PASSED           [ 25%]
tests/test_browser.py::test_timeout_handling PASSED                      [ 33%]
tests/test_scheduler_and_db.py::test_database_crud PASSED                [ 41%]
tests/test_scheduler_and_db.py::test_task_manager_toggle PASSED          [ 50%]
tests/test_scheduler_and_db.py::test_recovery_engine_classification PASSED [ 58%]
tests/test_scheduler_and_db.py::test_scheduler_immediate_task_run PASSED [ 66%]
tests/test_workflow_engine.py::test_workflow_yaml_parsing PASSED         [ 75%]
tests/test_workflow_engine.py::test_workflow_execution_success PASSED    [ 83%]
tests/test_workflow_engine.py::test_workflow_dry_run_protection PASSED   [ 91%]
tests/test_workflow_engine.py::test_workflow_verification_failure_stops_execution PASSED [100%]

============================= 12 passed in 15.75s =============================
```
