# SMART WEB AUTOMATION AGENT

## Tài liệu yêu cầu dự án dành cho AI Coding Agent

**Phiên bản:** 1.0\
**Ngày tạo:** 30/10/2026\
**Nền tảng ưu tiên:** Windows 11\
**Định hướng:** Local-first, có thể mở rộng lên cloud\
**Ngôn ngữ giao diện:** Tiếng Việt trước, hỗ trợ đa ngôn ngữ về sau

------------------------------------------------------------------------

# 1. Vai trò và nhiệm vụ của AI phát triển

Bạn là AI Software Architect kiêm Senior Full-Stack/Python Engineer.
Nhiệm vụ của bạn là thiết kế, xây dựng, kiểm thử và hoàn thiện một ứng
dụng có tên **Smart Web Automation Agent**.

Đây không phải công cụ auto-click đơn giản. Đây là hệ thống tự động hóa
trình duyệt có khả năng:

-   Thực hiện các quy trình trên website theo kịch bản.
-   Lên lịch và kích hoạt hành động tại thời điểm xác định.
-   Chuẩn bị trước phiên trình duyệt để giảm thao tác khởi tạo vào giờ
    cao điểm.
-   Theo dõi tiến trình và xác định chính xác bước đang thực hiện.
-   Phát hiện lỗi tải trang, timeout, mất kết nối và phản hồi máy chủ.
-   Khôi phục một cách có kiểm soát, tránh gửi hành động trùng lặp.
-   Lưu lịch sử, ảnh chụp màn hình, log và trạng thái nhiệm vụ.
-   Yêu cầu người dùng can thiệp khi gặp CAPTCHA, xác thực bổ sung hoặc
    hành động nhạy cảm.
-   Có thể mở rộng AI Agent để hỗ trợ xử lý giao diện thay đổi hoặc tình
    huống chưa được định nghĩa.

Các tình huống sử dụng tiêu biểu:

1.  Săn sale: mở trang sản phẩm đúng giờ, kiểm tra trạng thái, chọn biến
    thể, thêm giỏ hàng và tiếp tục quy trình mua hàng theo quyền được
    cấp.
2.  Đăng ký môn học: truy cập cổng trường, tìm học phần, chọn lớp theo
    thứ tự ưu tiên, kiểm tra kết quả đăng ký.
3.  Đặt vé/đặt lịch: chuẩn bị thông tin, theo dõi thời điểm mở bán và
    thực hiện các bước được website cho phép.
4.  Các quy trình web lặp lại khác do người dùng tự cấu hình.

**Mục tiêu tối ưu là hoàn thành nhiệm vụ hợp lệ, ổn định và có thể kiểm
chứng; không phải vượt qua cơ chế bảo vệ hoặc chiếm lợi thế bằng cách
gây tải bất thường cho website.**

------------------------------------------------------------------------

# 2. Nguyên tắc bắt buộc

## 2.1. Local-first

-   Ứng dụng phải chạy được trên máy Windows cá nhân mà không bắt buộc
    có cloud.
-   Không yêu cầu API AI trả phí để thực hiện các workflow cơ bản.
-   Có thể tích hợp Ollama và model local ở giai đoạn sau.
-   Thiết kế module độc lập để có thể đưa Scheduler hoặc dịch vụ điều
    phối lên cloud trong tương lai.

## 2.2. Workflow trước, AI sau

-   Các thao tác quan trọng phải được mô tả bằng workflow có cấu trúc.
-   Workflow là nguồn quyết định chính đối với thao tác có tính chính
    xác cao.
-   AI chỉ hỗ trợ phân tích tình huống bất thường, gợi ý cách xử lý hoặc
    hỗ trợ xây dựng workflow.
-   Không để model tự quyết định các hành động nhạy cảm mà không có
    chính sách và giới hạn rõ ràng.

## 2.3. Không click mù quáng

-   Ưu tiên locator theo role, label, text, placeholder hoặc thuộc tính
    ổn định.
-   Hạn chế dùng tọa độ màn hình.
-   Trước hành động quan trọng phải kiểm tra điều kiện và trạng thái.
-   Sau hành động phải xác minh kết quả bằng DOM, URL, thông báo hoặc dữ
    liệu trạng thái đáng tin cậy.
-   Không coi việc click thành công là bằng chứng hành động nghiệp vụ đã
    thành công.

## 2.4. An toàn và tuân thủ

Hệ thống chỉ được thao tác trên tài khoản và website mà người dùng có
quyền sử dụng.

Không triển khai tính năng: - Vượt CAPTCHA hoặc tự động giải CAPTCHA. -
Vượt hàng đợi ảo, queue token hoặc cơ chế giới hạn truy cập. - Xoay
IP/proxy, giả mạo fingerprint hoặc tạo nhiều tài khoản để né giới hạn. -
Bỏ qua giới hạn tốc độ, giới hạn mua hàng hoặc quy tắc đăng ký của
website. - Gửi request nội bộ trái phép hoặc khai thác endpoint không
dành cho người dùng. - Tự động xác nhận thanh toán, đặt hàng cuối cùng
hoặc đăng ký ràng buộc nếu người dùng chưa bật rõ quyền đó.

Khi gặp CAPTCHA, MFA, xác thực bổ sung, hàng đợi chính thức hoặc yêu cầu
xác nhận của website: - Giữ nguyên phiên hợp lệ. - Tạm dừng workflow. -
Hiển thị hướng dẫn để người dùng tự xử lý. - Tiếp tục sau khi người dùng
xác nhận. - Không tự ý reload nếu có nguy cơ mất vị trí hàng đợi hoặc
trạng thái.

Phải có giới hạn retry, backoff, jitter và concurrency để tránh gây tải
cho website. Tôn trọng điều khoản sử dụng, robots/rate limits khi áp
dụng và các thông báo của website.

------------------------------------------------------------------------

# 3. Kiến trúc tổng thể

Thiết kế theo kiến trúc module, tách biệt giao diện, điều phối, browser
automation, workflow, recovery và lưu trữ.

``` text
Smart Web Automation Agent
│
├── Desktop UI (PySide6)
│   ├── Dashboard
│   ├── Task Manager
│   ├── Workflow Builder
│   ├── Scheduler
│   ├── Live Monitor
│   ├── Recovery Center
│   ├── Execution History
│   └── Settings
│
├── Application/API Layer (FastAPI hoặc service nội bộ)
│
├── Core Engine
│   ├── Task Manager
│   ├── Workflow Engine
│   ├── Scheduler
│   ├── Browser Controller
│   ├── Action Engine
│   ├── State Manager
│   ├── Recovery Engine
│   ├── Policy & Approval Manager
│   └── Notification Manager
│
├── Integrations
│   ├── Playwright
│   ├── Chromium
│   ├── Ollama (optional, later phase)
│   └── Windows Notifications
│
└── Persistence
    ├── SQLite
    ├── Workflow definitions
    ├── Browser session metadata
    ├── Execution logs
    └── Screenshots / artifacts
```

## 3.1. Công nghệ đề xuất

  Thành phần           Công nghệ
  -------------------- -----------------------------------------------
  Ngôn ngữ chính       Python 3.12+
  Browser automation   Playwright
  Browser              Chromium trước, mở rộng browser khác sau
  Desktop UI           PySide6
  API/service nội bộ   FastAPI, chỉ khi cần
  Database             SQLite
  ORM/migration        SQLAlchemy + Alembic (nếu phù hợp)
  Scheduler            APScheduler hoặc scheduler service tự quản lý
  Logging              Python logging, log có cấu trúc
  Validation           Pydantic
  Testing              pytest
  AI local             Ollama, tùy chọn ở phase sau
  Packaging            PyInstaller ở giai đoạn hoàn thiện

Không cần triển khai toàn bộ công nghệ ngay từ đầu. Ưu tiên bộ khung
nhỏ, chạy được và dễ kiểm thử.

## 3.2. Yêu cầu môi trường phát triển

Môi trường mục tiêu: - Windows 11. - Python 3.12. - Có thể chạy trong
virtual environment. - Có thể sử dụng PowerShell hoặc CMD. - Không giả
định người dùng có quyền Administrator. - Các đường dẫn phải xử lý đúng
trên Windows. - Không hardcode đường dẫn máy cá nhân; dùng cấu hình và
thư mục ứng dụng.

------------------------------------------------------------------------

# 4. Các module chức năng

## 4.1. Task Manager

Cho phép người dùng tạo, sửa, sao chép, bật/tắt, chạy thử và xóa nhiệm
vụ.

Mỗi task cần có: - ID duy nhất. - Tên nhiệm vụ. - Mô tả. -
Website/domain mục tiêu. - Workflow được gắn. - Thời gian chạy hoặc lịch
chạy. - Múi giờ. - Mức ưu tiên. - Chính sách retry. - Chính sách yêu cầu
xác nhận. - Trạng thái hiện tại. - Thời điểm tạo/cập nhật. - Lịch sử
thực thi.

Trạng thái task đề xuất:

`DRAFT`, `READY`, `SCHEDULED`, `PREPARING`, `RUNNING`, `WAITING_USER`,
`SUCCEEDED`, `FAILED`, `CANCELLED`, `PAUSED`.

Không dùng một trường trạng thái chung để biểu diễn đồng thời trạng thái
task và trạng thái từng action.

## 4.2. Workflow Engine

Workflow là chuỗi action có cấu trúc, có thể lưu, tái sử dụng và phiên
bản hóa.

Các action cơ bản: - `navigate` - `wait_for` - `click` - `fill` -
`select_option` - `check` - `uncheck` - `read_text` - `read_attribute` -
`screenshot` - `assert` - `branch` - `loop` với giới hạn rõ ràng -
`wait` - `notify` - `request_user_input` - `pause` - `stop`

Mỗi action cần có: - ID. - Loại action. - Tham số. - Timeout. - Điều
kiện trước khi chạy. - Điều kiện xác minh sau khi chạy. - Chính sách
retry riêng nếu phù hợp. - Mức độ rủi ro. - Thông tin lỗi và thời gian
thực thi.

Ví dụ workflow minh họa:

``` yaml
name: Check course registration
version: 1
steps:
  - id: open_portal
    action: navigate
    url: "https://example.edu.vn"
    verify:
      type: url_contains
      value: "example.edu.vn"

  - id: wait_dashboard
    action: wait_for
    locator:
      role: heading
      name: "Trang chủ"
    timeout_ms: 15000

  - id: open_registration
    action: click
    locator:
      role: link
      name: "Đăng ký học phần"
    verify:
      type: visible
      locator:
        text: "Danh sách học phần"

  - id: pause_for_review
    action: request_user_input
    message: "Kiểm tra thông tin trước khi tiếp tục đăng ký."
```

Ví dụ chỉ mang tính minh họa. Không giả định cấu trúc website thực tế.

### Workflow Builder

Giai đoạn đầu có thể cung cấp: - Danh sách step. - Thêm/xóa/sắp xếp
step. - Chỉnh sửa tham số. - Chạy thử từng step. - Chạy thử toàn
workflow. - Xem log và screenshot. - Import/export YAML hoặc JSON có
validation.

Không cần xây dựng visual drag-and-drop phức tạp ngay trong MVP.

## 4.3. Browser Controller

Dùng Playwright để: - Khởi chạy Chromium. - Tạo browser context riêng
theo profile. - Mở và quản lý tab. - Điều hướng website. - Tìm phần
tử. - Click, nhập liệu, chọn option. - Đọc DOM và trạng thái trang. -
Theo dõi navigation, request, response và lỗi mạng. - Chụp screenshot. -
Đóng hoặc khôi phục browser theo chính sách.

### Quản lý session

-   Dùng Playwright persistent context hoặc storage state theo thiết kế
    an toàn.
-   Session phải được phân tách theo profile.
-   Không ghi password, cookie hoặc token dạng plaintext vào log.
-   Có tùy chọn người dùng tự đăng nhập lần đầu.
-   Nếu session hết hạn, dừng và yêu cầu người dùng đăng nhập lại.
-   Không tự động vượt MFA hoặc CAPTCHA.

### Locator strategy

Thứ tự ưu tiên: 1. Role + accessible name. 2. Label. 3. Placeholder. 4.
Text có phạm vi rõ ràng. 5. Test ID. 6. CSS selector ổn định. 7. XPath
chỉ khi thật sự cần. 8. Tọa độ màn hình là phương án cuối cùng và phải
được đánh dấu không ổn định.

## 4.4. Scheduler

Chức năng: - Lên lịch chạy một lần. - Lên lịch định kỳ. - Hỗ trợ
timezone. - Chạy nhiều task theo thứ tự ưu tiên. - Cho phép hủy, tạm
dừng và chạy ngay. - Khôi phục lịch sau khi ứng dụng khởi động lại. -
Hiển thị thời gian còn lại. - Lưu trạng thái lịch vào database.

### Pre-warming

Với task có giờ kích hoạt cụ thể, hệ thống có thể chuẩn bị trước: - Mở
browser. - Khôi phục session hợp lệ. - Điều hướng đến trang phù hợp. -
Kiểm tra các thành phần cần thiết. - Kiểm tra kết nối. - Chờ đến thời
điểm đã cấu hình.

Không thực hiện hành động nghiệp vụ sớm hơn thời điểm được phép. Không
gửi request liên tục để dò slot. Tần suất kiểm tra phải cấu hình được,
có giới hạn và tôn trọng chính sách website.

### Độ chính xác thời gian

-   Dùng đồng hồ hệ điều hành và timezone rõ ràng.
-   Lưu thời điểm dưới dạng UTC trong database; hiển thị theo timezone
    người dùng.
-   Ghi lại thời điểm dự kiến và thời điểm thực tế.
-   Không cam kết độ chính xác tuyệt đối ở mức millisecond vì Windows,
    scheduler, trình duyệt và mạng có độ trễ.
-   Có thể dùng monotonic clock cho các khoảng chờ trong tiến trình.

## 4.5. Recovery Engine

Đây là module ưu tiên cao.

Recovery Engine phải phân loại lỗi trước khi quyết định hành động. Không
được mặc định reload với mọi lỗi.

### Phân loại tình huống

  -----------------------------------------------------------------------
  Tình huống                          Hành động
  ----------------------------------- -----------------------------------
  Locator chưa xuất hiện              Chờ trong giới hạn timeout, chụp
                                      ảnh và báo lỗi nếu hết hạn

  Trang đang tải                      Chờ điều kiện cụ thể, tránh chỉ dựa
                                      vào `networkidle`

  Request timeout                     Kiểm tra trạng thái nghiệp vụ trước
                                      khi gửi lại

  HTTP 500/502/503/504                Backoff có giới hạn, kiểm tra lại
                                      trạng thái

  Mất kết nối                         Chờ kết nối phục hồi rồi kiểm tra
                                      trạng thái

  Session hết hạn                     Dừng và yêu cầu đăng nhập lại

  CAPTCHA/MFA                         Tạm dừng, yêu cầu người dùng

  Website có queue                    Giữ nguyên session và trạng thái
                                      queue; không reload nếu có nguy cơ
                                      mất vị trí

  Action đã thành công                Đánh dấu thành công, không thực
                                      hiện lại

  Không xác định được kết quả         Chuyển trạng thái `UNKNOWN` hoặc
                                      `NEEDS_REVIEW`, không tự gửi lại
                                      action rủi ro
  -----------------------------------------------------------------------

### Retry policy

Mỗi retry phải có: - Số lần thử tối đa. - Timeout. - Delay. -
Exponential backoff. - Jitter. - Loại lỗi được phép retry. - Điều kiện
dừng. - Giới hạn tổng thời gian.

Không retry vô hạn. Không tăng tốc độ retry khi website đang báo quá
tải.

### Idempotency và duplicate prevention

Đối với action có thể tạo tác động nghiệp vụ: - Kiểm tra trạng thái
trước khi gửi. - Tạo execution/action ID. - Lưu trạng thái trước và sau
hành động. - Nếu timeout sau khi gửi, xác minh kết quả trước khi thử
lại. - Nếu không thể xác minh, yêu cầu người dùng kiểm tra. - Chỉ dùng
idempotency key khi website/API chính thức hỗ trợ. - Không giả định
click hoặc request có thể thực hiện lặp lại an toàn.

## 4.6. State Manager

State Manager lưu tiến trình có thể khôi phục.

Cần lưu: - Task ID. - Execution ID. - Workflow version. - Current step
ID. - Step status. - Step input/output đã được lọc dữ liệu nhạy cảm. -
Start/end timestamp. - Retry count. - Error category. - Screenshot
reference. - Browser profile reference. - Last known URL. - Kết quả xác
minh gần nhất.

Khi ứng dụng khởi động lại: - Đọc các execution đang chạy dở. - Không tự
động chạy lại action có thể gây tác động nghiệp vụ. - Khôi phục ở trạng
thái an toàn. - Yêu cầu xác minh hoặc người dùng quyết định nếu kết quả
cuối cùng chưa rõ.

## 4.7. Monitoring và Notification

Dashboard cần hiển thị: - Task đang chạy. - Task sắp chạy. - Task thành
công/thất bại. - Step hiện tại. - Website hiện tại. - Thời gian chạy. -
Số lần retry. - Lỗi gần nhất. - Yêu cầu người dùng can thiệp.

Live Monitor: - Hiển thị screenshot mới nhất. - Hiển thị log theo thời
gian. - Hiển thị trạng thái browser. - Có nút Pause, Resume, Stop. -
Không hiển thị bí mật như password, cookie hoặc token.

Notification: - Task bắt đầu. - Task hoàn thành. - Task thất bại. - Cần
người dùng đăng nhập/xác minh. - Cần xác nhận hành động quan trọng.

------------------------------------------------------------------------

# 5. Chính sách phê duyệt hành động

Phân loại action theo rủi ro:

  -----------------------------------------------------------------------
  Mức                     Ví dụ                   Chính sách mặc định
  ----------------------- ----------------------- -----------------------
  Low                     Mở trang, tìm kiếm, đọc Tự động
                          dữ liệu                 

  Medium                  Thêm vào giỏ hàng, chọn Cho phép theo cấu hình
                          lớp dự kiến             

  High                    Gửi đăng ký cuối cùng,  Yêu cầu xác nhận
                          đặt hàng                

  Critical                Thanh toán, hành động   Luôn yêu cầu xác nhận
                          không thể hoàn tác      rõ ràng
  -----------------------------------------------------------------------

Người dùng có thể thay đổi chính sách theo từng workflow, nhưng không
được bỏ qua xác nhận đối với hành động thanh toán/critical trong cấu
hình mặc định.

Cần có chế độ `Dry Run`: - Mô phỏng hoặc chạy đến trước bước tác động. -
Hiển thị các action dự kiến. - Không gửi hành động cuối cùng. - Giúp
người dùng kiểm tra workflow trước khi lên lịch thật.

------------------------------------------------------------------------

# 6. Giao diện người dùng

Thiết kế hiện đại, rõ ràng, ưu tiên desktop Windows. Giao diện tiếng
Việt trước.

## 6.1. Dashboard

Hiển thị: - Tổng số task. - Task đang chạy. - Task sắp chạy. - Task
thành công/thất bại. - Lịch chạy gần nhất. - Hoạt động gần đây.

## 6.2. Task Manager

-   Danh sách task.
-   Tìm kiếm và lọc.
-   Tạo task.
-   Chỉnh sửa.
-   Sao chép.
-   Bật/tắt.
-   Chạy ngay.
-   Dừng.
-   Xem lịch sử.

## 6.3. Workflow Builder

-   Danh sách step.
-   Chỉnh sửa action.
-   Cấu hình locator.
-   Cấu hình điều kiện.
-   Cấu hình timeout/retry.
-   Chạy thử từng step.
-   Dry Run.
-   Import/export workflow.

## 6.4. Scheduler

-   Calendar hoặc timeline.
-   Danh sách task sắp chạy.
-   Đếm ngược.
-   Trạng thái chuẩn bị browser.
-   Cảnh báo trùng lịch hoặc xung đột profile.

## 6.5. Live Monitor

-   Screenshot.
-   Current URL.
-   Current step.
-   Event log.
-   Retry count.
-   Pause/Resume/Stop.

## 6.6. Recovery Center

-   Lỗi đã phát hiện.
-   Phân loại nguyên nhân.
-   Hành động recovery đã thử.
-   Trạng thái hiện tại.
-   Đề xuất bước tiếp theo.
-   Nút tiếp tục sau khi người dùng xử lý.

## 6.7. Settings

-   Browser executable/channel.
-   Browser profile.
-   Thư mục dữ liệu.
-   Timezone.
-   Retry defaults.
-   Notification.
-   AI provider/model (giai đoạn sau).
-   Chính sách phê duyệt.

------------------------------------------------------------------------

# 7. Database đề xuất

Dùng SQLite cho MVP.

Các bảng dự kiến:

## `tasks`

-   `id`
-   `name`
-   `description`
-   `workflow_id`
-   `schedule_config`
-   `priority`
-   `approval_policy`
-   `enabled`
-   `created_at`
-   `updated_at`

## `workflows`

-   `id`
-   `name`
-   `version`
-   `definition_json`
-   `created_at`
-   `updated_at`

## `executions`

-   `id`
-   `task_id`
-   `workflow_version`
-   `status`
-   `started_at`
-   `finished_at`
-   `current_step_id`
-   `last_error`
-   `browser_profile_id`

## `step_executions`

-   `id`
-   `execution_id`
-   `step_id`
-   `status`
-   `attempt`
-   `started_at`
-   `finished_at`
-   `result_json`
-   `error_category`

## `browser_profiles`

-   `id`
-   `name`
-   `storage_reference`
-   `created_at`
-   `updated_at`

## `artifacts`

-   `id`
-   `execution_id`
-   `step_execution_id`
-   `type`
-   `file_path`
-   `created_at`

## `app_settings`

-   `key`
-   `value_json`
-   `updated_at`

Yêu cầu: - Có migration hoặc version database. - Có foreign key. - Có
index cho truy vấn lịch và execution. - Không lưu credential dạng
plaintext. - Có chính sách dọn dẹp screenshot/log cũ. - Database không
được chứa dữ liệu bí mật không cần thiết.

------------------------------------------------------------------------

# 8. Bảo mật

-   Không hardcode API key, password hoặc token.
-   Không ghi credential vào log.
-   Hạn chế quyền truy cập thư mục profile và dữ liệu ứng dụng.
-   Tách browser profile theo tài khoản/website khi cần.
-   Không expose FastAPI ra mạng LAN/Internet mặc định.
-   Nếu có local API, bind vào `127.0.0.1` và có cơ chế bảo vệ phù hợp.
-   Validate workflow import để tránh thực thi nội dung tùy ý.
-   Giới hạn URL/domain được phép thao tác theo cấu hình task.
-   Có nút Stop khẩn cấp.
-   Không cho workflow tự chạy lệnh shell tùy ý.
-   Có timeout và giới hạn vòng lặp để tránh treo ứng dụng.

------------------------------------------------------------------------

# 9. Lộ trình phát triển

Không xây dựng tất cả cùng lúc. Phát triển theo từng phase, mỗi phase
phải chạy được và có kiểm thử.

## Phase 1 --- Browser Automation Foundation (MVP đầu tiên)

Mục tiêu: Có thể mở trình duyệt và thao tác website bằng Python.

Công việc: 1. Tạo project structure. 2. Tạo virtual environment và
dependency file. 3. Cài đặt Playwright và Chromium. 4. Tạo Browser
Controller. 5. Mở URL. 6. Tìm locator và click. 7. Nhập liệu. 8. Chụp
screenshot. 9. Ghi log. 10. Đóng browser an toàn. 11. Tạo demo workflow
trên website thử nghiệm do người dùng kiểm soát.

Acceptance criteria: - Chạy được bằng một lệnh rõ ràng. - Mở được
Chromium. - Truy cập được URL thử nghiệm. - Thực hiện được click và
fill. - Chụp được screenshot. - Ghi được log thành công/thất bại. - Có
xử lý timeout. - Không cần AI hoặc cloud. - Có README hướng dẫn cài đặt
và chạy.

## Phase 2 --- Workflow Engine

-   Định nghĩa workflow bằng JSON/YAML.
-   Action registry.
-   Step execution.
-   Assertion/verification.
-   Branch cơ bản.
-   Chạy thử từng step.
-   Dry Run.
-   Import/export.
-   Unit test.

Acceptance criteria: người dùng tạo được workflow gồm nhiều bước và chạy
lại được.

## Phase 3 --- Scheduler

-   Lưu lịch trong SQLite.
-   Chạy một lần và định kỳ.
-   Pre-warming browser.
-   Khôi phục lịch sau restart.
-   Pause/resume/cancel.
-   Timezone rõ ràng.
-   Kiểm thử lệch thời gian và trùng lịch.

Acceptance criteria: task được kích hoạt đúng lịch trong giới hạn thực
tế của hệ điều hành, có log thời gian dự kiến/thực tế.

## Phase 4 --- Recovery Engine

-   Phân loại lỗi.
-   Retry policy.
-   Exponential backoff + jitter.
-   State persistence.
-   Duplicate prevention.
-   Phát hiện session hết hạn.
-   Pause khi CAPTCHA/MFA/queue.
-   Recovery test bằng website mô phỏng.

Acceptance criteria: - Không retry vô hạn. - Không gửi lại action có kết
quả chưa rõ. - Phân biệt được lỗi có thể retry và lỗi cần người dùng. -
Có thể phục hồi an toàn sau khi ứng dụng restart.

## Phase 5 --- Desktop UI

-   Dashboard.
-   Task Manager.
-   Workflow Builder.
-   Scheduler.
-   Live Monitor.
-   Recovery Center.
-   Settings.
-   Notification.

Acceptance criteria: người dùng có thể tạo, lên lịch, theo dõi và dừng
task qua giao diện mà không cần sửa code.

## Phase 6 --- AI Agent

-   Tích hợp Ollama tùy chọn.
-   AI đọc mô tả lỗi và log đã lọc.
-   AI đề xuất cách sửa workflow.
-   AI hỗ trợ nhận diện thay đổi giao diện.
-   AI không tự thực hiện hành động rủi ro nếu chưa được policy cho
    phép.
-   Có giới hạn thời gian và fallback khi model không phản hồi.

Acceptance criteria: tắt AI thì các workflow cơ bản vẫn hoạt động bình
thường.

## Phase 7 --- Packaging và mở rộng

-   Build ứng dụng Windows.
-   Khởi động cùng Windows tùy chọn.
-   Backup/restore database.
-   Import/export cấu hình.
-   Chuẩn bị kiến trúc cloud scheduler trong tương lai.
-   Không yêu cầu cloud trong bản local.

------------------------------------------------------------------------

# 10. Kiểm thử bắt buộc

Không thử nghiệm đầu tiên trên website săn sale hoặc cổng đăng ký thật.

Tạo website test local hoặc dùng website demo do người phát triển kiểm
soát, có thể mô phỏng:

1.  Trang tải chậm.
2.  Element xuất hiện trễ.
3.  HTTP 500/502/503.
4.  Request timeout.
5.  Mất kết nối trong lúc workflow chạy.
6.  Session hết hạn.
7.  Popup bất ngờ.
8.  Element đổi tên hoặc biến mất.
9.  Action gửi thành công nhưng response bị trì hoãn.
10. Ứng dụng bị đóng giữa workflow.
11. Hai task cùng đến lịch.
12. Queue trạng thái chờ.
13. CAPTCHA/MFA giả lập để kiểm tra cơ chế pause.
14. Website trả về kết quả không rõ ràng sau khi gửi action.

Cần có unit test, integration test và test recovery.

Không kiểm thử bằng cách tạo tải lớn lên website bên thứ ba.

------------------------------------------------------------------------

# 11. Yêu cầu về cấu trúc source code

Có thể bắt đầu với cấu trúc:

``` text
smart-web-automation/
│
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── task_manager.py
│   │   ├── workflow_engine.py
│   │   ├── action_registry.py
│   │   ├── scheduler.py
│   │   ├── state_manager.py
│   │   ├── recovery_engine.py
│   │   └── approval_manager.py
│   │
│   ├── browser/
│   │   ├── browser_controller.py
│   │   ├── session_manager.py
│   │   ├── locator.py
│   │   └── network_monitor.py
│   │
│   ├── actions/
│   │   ├── navigation.py
│   │   ├── interaction.py
│   │   ├── extraction.py
│   │   ├── verification.py
│   │   └── user_interaction.py
│   │
│   ├── database/
│   │   ├── models.py
│   │   ├── repository.py
│   │   └── migrations/
│   │
│   ├── ui/
│   │   ├── main_window.py
│   │   ├── views/
│   │   └── widgets/
│   │
│   ├── notifications/
│   │   └── windows_toast.py
│   │
│   ├── config/
│   │   └── settings.py
│   │
│   └── utils/
│       ├── logging_config.py
│       └── time_utils.py
│
├── workflows/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── data/
├── artifacts/
├── logs/
├── docs/
├── .env.example
├── .gitignore
├── requirements.txt
├── pyproject.toml
└── README.md
```

Có thể điều chỉnh cấu trúc nếu có lý do kỹ thuật rõ ràng, nhưng phải giữ
ranh giới module và không gom toàn bộ logic vào một file.

------------------------------------------------------------------------

# 12. Cách AI phải làm việc với người dùng

Đây là yêu cầu rất quan trọng.

Người dùng muốn phát triển dự án từng bước, ưu tiên thao tác bằng
command line và xác nhận trước khi chuyển bước tiếp theo.

Vì vậy:

1.  Trước tiên, đọc toàn bộ tài liệu này.
2.  Kiểm tra môi trường thực tế: Windows, Python, thư mục dự án,
    dependency hiện có.
3.  Đề xuất cấu trúc và giải thích ngắn gọn.
4.  Không tự ý tạo một lượng lớn file trước khi thống nhất cấu trúc
    Phase 1.
5.  Chia công việc thành các bước nhỏ.
6.  Mỗi bước chỉ đưa ra những lệnh cần thiết.
7.  Chờ người dùng chạy và phản hồi kết quả trước khi tiếp tục.
8.  Nếu gặp lỗi, xử lý lỗi hiện tại trước; không bỏ qua để chuyển bước.
9.  Không giả định lệnh đã chạy thành công nếu chưa có kết quả.
10. Khi sửa code, cung cấp nội dung hoàn chỉnh của file hoặc patch đủ rõ
    để áp dụng.
11. Sau mỗi module, chạy test và báo kết quả.
12. Cập nhật README và tiến độ dự án sau mỗi phase.
13. Không tự ý đổi công nghệ hoặc kiến trúc cốt lõi nếu chưa giải thích
    lý do.
14. Nếu thiếu thông tin quan trọng, hỏi một câu rõ ràng thay vì tự suy
    đoán.

## Quy tắc tiến độ

Duy trì `docs/PROJECT_STATUS.md` gồm: - Phase hiện tại. - Các việc đã
hoàn thành. - Các việc chưa hoàn thành. - File đã tạo/sửa. - Lệnh đã
chạy. - Kết quả test. - Lỗi đang tồn tại. - Bước tiếp theo.

Mỗi lần kết thúc một phiên làm việc, cập nhật trạng thái để phiên sau có
thể tiếp tục mà không phải làm lại.

------------------------------------------------------------------------

# 13. Nhiệm vụ đầu tiên dành cho AI

**Chỉ bắt đầu Phase 1. Không triển khai toàn bộ dự án ngay.**

Thực hiện theo thứ tự:

1.  Đọc tài liệu yêu cầu.
2.  Kiểm tra môi trường Windows và Python.
3.  Kiểm tra xem thư mục dự án đã tồn tại chưa.
4.  Đề xuất vị trí lưu source code.
5.  Đưa ra cấu trúc Phase 1 tối giản.
6.  Giải thích ngắn gọn từng thành phần.
7.  Đưa lệnh đầu tiên để người dùng thực hiện.
8.  Chờ người dùng xác nhận kết quả rồi mới tiếp tục.

Phase 1 phải tạo ra một chương trình demo có thể: - Khởi chạy
Chromium. - Truy cập website thử nghiệm. - Tìm một phần tử bằng
locator. - Thực hiện một thao tác click hoặc nhập liệu. - Xác minh kết
quả. - Chụp screenshot. - Ghi log. - Đóng trình duyệt an toàn.

**Không tích hợp AI, Scheduler, Recovery Engine phức tạp hoặc giao diện
hoàn chỉnh trong bước đầu tiên.** Hãy xây dựng nền tảng browser
automation nhỏ, sạch, có test và có thể mở rộng.

------------------------------------------------------------------------

# 14. Tiêu chí thành công cuối cùng

Dự án được xem là đạt mục tiêu khi:

-   Người dùng tạo được workflow cho một website.
-   Có thể lưu workflow và tái sử dụng.
-   Có thể đặt lịch chạy tại thời điểm cụ thể.
-   Browser được chuẩn bị trước khi đến giờ chạy.
-   Hệ thống theo dõi được từng bước.
-   Có thể phát hiện lỗi và phân loại nguyên nhân.
-   Có thể retry an toàn với lỗi phù hợp.
-   Không gửi hành động nghiệp vụ trùng khi kết quả chưa rõ.
-   Có thể tạm dừng để người dùng xử lý CAPTCHA/MFA hoặc xác nhận.
-   Có thể khôi phục trạng thái sau khi ứng dụng khởi động lại.
-   Có dashboard để quản lý và theo dõi.
-   Chạy local trên Windows mà không bắt buộc cloud hoặc API trả phí.
-   Có tài liệu cài đặt, sử dụng, kiểm thử và khắc phục lỗi.

**Hãy ưu tiên độ tin cậy, khả năng kiểm chứng và an toàn hơn việc cố
gắng thực hiện thật nhiều thao tác trong thời gian ngắn.**
