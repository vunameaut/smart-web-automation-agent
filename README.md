# Smart Web Automation Agent

Hệ thống tự động hóa trình duyệt đáng tin cậy, cục bộ (**Local-first**) trên nền tảng **Windows 11** và **Python 3.12+**, xây dựng bằng **Playwright**, **SQLAlchemy (SQLite)**, **APScheduler**, và giao diện **PySide6**.

Tuân thủ tuyệt đối tài liệu đặc tả [SMART_WEB_AUTOMATION_AGENT_PROJECT_SPEC.md](SMART_WEB_AUTOMATION_AGENT_PROJECT_SPEC.md).

---

## 🌟 Tính năng nổi bật

1. **Local-first & Bảo mật cao:**
   - Hoàn toàn độc lập, lưu trữ dữ liệu tại máy cá nhân với SQLite (`data/autoweb.db`).
   - Tự động làm mờ (redact) mật khẩu, token, secret trong file log `logs/agent.log`.
   - **Xác thực Target Domains:** Ngăn chặn việc workflow tự ý điều hướng tới domain lạ ngoài whitelist quy định.
   - **Lưu trữ phiên đăng nhập (Playwright Storage State):** Lưu cookies/session tại `data/browser_profiles/` giúp duy trì trạng thái đăng nhập giữa các lần chạy.

2. **Quy tắc cốt lõi: "Không click mù quáng":**
   - Bộ phân giải Locator ưu tiên chuẩn Accessibility: `Role` > `Label` > `Placeholder` > `Text` > `Test ID` > `CSS`.
   - Kiểm tra điều kiện khả dụng (`visible`, `enabled`) trước khi click. Từ chối click nút `Disabled` để bảo vệ phiên làm việc.
   - Luôn xác minh kết quả nghiệp vụ từ DOM sau khi thực hiện hành động.

3. **Workflow Engine & Action Registry:**
   - Định nghĩa kịch bản bằng file YAML/JSON ([`workflows/course_registration.yaml`](workflows/course_registration.yaml)).
   - Đầy đủ các Action cơ bản: `navigate`, `click`, `fill`, `wait_for`, `read_text`, `screenshot`, `wait`.
   - Hỗ trợ cơ chế **Dry Run** (chạy thử an toàn: tự động dừng/bỏ qua các bước High/Critical Risk như đặt hàng, submit form cuối cùng).

4. **Recovery Engine & Scheduler:**
   - Phân loại lỗi thông minh: `CAPTCHA_OR_MFA`, `QUEUE_DETECTED`, `SESSION_EXPIRED`, `SERVER_ERROR_5XX`, `LOCATOR_NOT_FOUND`.
   - Exponential backoff + ngẫu nhiên Jitter.
   - Khởi động bộ lập lịch `APScheduler` tự động khi mở app, nạp lại lịch trình từ cơ sở dữ liệu.
   - Hỗ trợ tính năng **Pre-warming**: Khởi động trước trình duyệt và điều hướng sớm để chuẩn bị giờ cao điểm.

5. **Giao diện Desktop hiện đại (PySide6 Pro Control Center):**
   - **Bảng Điều Khiển (Dashboard)**: Thống kê số lượng nhiệm vụ, trạng thái chạy và hướng dẫn sử dụng nhanh.
   - **Quản Lý Nhiệm Vụ (Task Manager)**: Tạo nhiệm vụ, cấu hình **Biến số (Variables)** dạng JSON, Đặt lịch chạy tự động, chạy thử an toàn (Dry Run) hoặc chạy thật trên background thread không đơ UI.
   - **Trình Tạo Kịch Bản (Workflow Builder)**: Hộp thoại trực quan thêm/sửa/xóa từng bước thao tác mà không cần gõ code.
   - **Giám Sát Realtime**: Xem log trực tiếp và xem trước ảnh chụp màn hình chứng từ mới nhất.

---

## 📁 Cấu trúc thư mục dự án

```text
autoweb/
│
├── app/
│   ├── __init__.py
│   ├── actions/                    # Action Engine & Implementation
│   │   ├── __init__.py
│   │   ├── base.py                 # BaseAction, ActionContext & DomainSecurity
│   │   └── standard_actions.py     # Navigate, Click, Fill, ReadText, Screenshot...
│   │
│   ├── browser/                    # Browser Controller & Locator
│   │   ├── __init__.py
│   │   ├── browser_controller.py   # Quản lý Chromium, storage_state, context
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
│   │   ├── workflow_engine.py      # Điều phối thực thi, xác minh & Recovery
│   │   ├── recovery_engine.py      # Phân loại lỗi, retry policy, backoff + jitter
│   │   ├── scheduler.py            # APScheduler & Pre-warming browser
│   │   └── task_manager.py         # Quản lý CRUD nhiệm vụ & biến số
│   │
│   ├── database/                   # SQLite Persistence
│   │   ├── __init__.py
│   │   ├── database.py             # SQLAlchemy Engine & Session
│   │   ├── models.py               # Bảng tasks, workflows, executions, artifacts...
│   │   └── repository.py           # Repository truy cập dữ liệu
│   │
│   ├── ui/                         # Desktop UI
│   │   ├── __init__.py
│   │   ├── main_window.py          # PySide6 MainWindow (Pro Control Center)
│   │   ├── step_dialog.py          # Hộp thoại thêm/sửa từng bước thao tác
│   │   ├── task_variables_dialog.py# Hộp thoại cấu hình biến số cho Task
│   │   └── task_worker.py          # Background QThread chạy task không đơ GUI
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
│   ├── test_domain_security.py     # Test kiểm tra an toàn Domain
│   ├── test_scheduler_and_db.py    # Test SQLite CRUD, Scheduler, Recovery
│   ├── test_ui_step_editor.py      # Test Hộp thoại cấu hình Step UI
│   └── test_workflow_engine.py     # Test Workflow Engine, YAML, Dry-run
│
├── artifacts/
│   └── screenshots/                # Thư mục lưu ảnh chụp màn hình khi chạy/lỗi
├── data/
│   ├── autoweb.db                  # Database SQLite cục bộ
│   └── browser_profiles/           # Thư mục lưu session state / cookies
├── logs/
│   └── agent.log                   # File log có cấu trúc
│
├── main.py                         # Điểm vào chính của ứng dụng (UI / CLI)
├── demo_phase1.py                  # Script demo thực tế mở trình duyệt trực quan
├── requirements.txt                # Danh mục thư viện phụ thuộc (Pinned versions)
├── pyproject.toml                  # Cấu hình dự án chuẩn build & dev
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

# Cài đặt toàn bộ thư viện (các phiên bản đã được ghim chặt chẽ)
pip install -r requirements.txt
# Hoặc cài đặt qua pyproject.toml:
pip install .

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
- **Liệt kê danh sách tất cả các Task kèm ID để chạy:**
  ```powershell
  python main.py --list-tasks
  ```
- **Kích hoạt chạy ngay một task qua dòng lệnh:**
  ```powershell
  python main.py --run-task <TASK_ID>
  ```
  *(Thêm cờ `--dry-run` để chạy thử an toàn)*

### 4. Chạy toàn bộ Test tự động (Pytest)

Chạy tất cả 16 bài kiểm thử tự động bao quát toàn bộ các tầng kiến trúc:
```powershell
pytest tests/ -v
```

---

## 📋 Kết quả kiểm thử tự động (16/16 Tests Passed)

```text
tests/test_browser.py::test_browser_lifecycle PASSED                     [  6%]
tests/test_browser.py::test_navigation_and_interactions PASSED           [ 12%]
tests/test_browser.py::test_disabled_element_protection PASSED           [ 18%]
tests/test_browser.py::test_timeout_handling PASSED                      [ 25%]
tests/test_domain_security.py::test_target_domains_security_allow PASSED [ 31%]
tests/test_domain_security.py::test_target_domains_security_block PASSED [ 37%]
tests/test_scheduler_and_db.py::test_database_crud PASSED                [ 43%]
tests/test_scheduler_and_db.py::test_task_manager_toggle PASSED          [ 50%]
tests/test_scheduler_and_db.py::test_recovery_engine_classification PASSED [ 56%]
tests/test_scheduler_and_db.py::test_scheduler_immediate_task_run PASSED [ 62%]
tests/test_ui_step_editor.py::test_step_editor_dialog_creation PASSED    [ 68%]
tests/test_ui_step_editor.py::test_step_editor_dialog_edit_mode PASSED   [ 75%]
tests/test_workflow_engine.py::test_workflow_yaml_parsing PASSED         [ 81%]
tests/test_workflow_engine.py::test_workflow_execution_success PASSED    [ 87%]
tests/test_workflow_engine.py::test_workflow_dry_run_protection PASSED   [ 93%]
tests/test_workflow_engine.py::test_workflow_verification_failure_stops_execution PASSED [100%]

============================= 16 passed in 16.35s =============================
```
