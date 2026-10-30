"""Smart Web Automation Agent - PySide6 Pro Control Center UI."""

import sys
import json
from pathlib import Path
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QTextEdit,
    QMessageBox,
    QGroupBox,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QDialog,
    QInputDialog,
    QFormLayout,
    QCheckBox,
    QSplitter,
    QFrame,
    QDateTimeEdit,
)
from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtGui import QPixmap

from app.config import get_settings
from app.database.repository import Repository
from app.database.database import init_db
from app.core.task_manager import TaskManager
from app.core.workflow_models import WorkflowDefinition, WorkflowStep
from app.ui.step_dialog import StepEditorDialog
from app.ui.task_worker import TaskExecutionWorker
from app.ui.task_variables_dialog import TaskVariablesDialog
from app.ui.scheduler_thread import SchedulerThread
from app.utils.logging_config import get_logger

logger = get_logger("autoweb.ui")


class CreateTaskDialog(QDialog):
    """Hộp thoại tạo nhiệm vụ mới."""

    def __init__(self, parent=None, workflows=None):
        super().__init__(parent)
        self.setWindowTitle("➕ Thêm Nhiệm Vụ Mới")
        self.resize(560, 520)
        self.workflows = workflows or []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        info_box = QLabel("Điền thông tin nhiệm vụ, biến dữ liệu và thiết lập lịch chạy:")
        info_box.setStyleSheet("color: #94a3b8; font-size: 13px; margin-bottom: 10px;")
        layout.addWidget(info_box)

        form = QFormLayout()
        
        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("VD: Đăng ký học phần tín chỉ...")
        form.addRow("Tên nhiệm vụ (*):", self.txt_name)

        self.cbo_workflow = QComboBox()
        for wf in self.workflows:
            self.cbo_workflow.addItem(f"{wf.name} (v{wf.version})", wf.id)
        form.addRow("Quy trình gắn kèm (*):", self.cbo_workflow)

        self.txt_desc = QLineEdit()
        self.txt_desc.setPlaceholderText("Mô tả mục tiêu của nhiệm vụ...")
        form.addRow("Mô tả:", self.txt_desc)

        self.spin_priority = QSpinBox()
        self.spin_priority.setRange(1, 10)
        self.spin_priority.setValue(1)
        form.addRow("Mức độ ưu tiên (1-10):", self.spin_priority)

        # Biến dữ liệu JSON
        self.txt_vars = QTextEdit()
        self.txt_vars.setPlaceholderText('{\n  "portal_url": "https://example.com",\n  "student_name": "Nguyễn Văn A"\n}')
        self.txt_vars.setMaximumHeight(90)
        form.addRow("Biến dữ liệu (JSON):", self.txt_vars)

        # Đặt lịch chạy
        self.chk_schedule = QCheckBox("Lên lịch chạy tự động")
        self.chk_schedule.toggled.connect(self._toggle_schedule)
        form.addRow("Đặt lịch:", self.chk_schedule)

        self.dt_run_at = QDateTimeEdit()
        self.dt_run_at.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        self.dt_run_at.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.dt_run_at.setEnabled(False)
        form.addRow("Thời gian chạy:", self.dt_run_at)

        self.chk_enabled = QCheckBox("Kích hoạt nhiệm vụ ngay")
        self.chk_enabled.setChecked(True)
        form.addRow("Trạng thái:", self.chk_enabled)

        layout.addLayout(form)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_cancel = QPushButton("Hủy bỏ")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("💾 Lưu Nhiệm Vụ")
        btn_save.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold; padding: 8px 16px;")
        btn_save.clicked.connect(self._validate_and_accept)

        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

    def _toggle_schedule(self, checked):
        self.dt_run_at.setEnabled(checked)

    def _validate_and_accept(self):
        if not self.txt_name.text().strip():
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập Tên nhiệm vụ.")
            return
        if self.cbo_workflow.count() == 0:
            QMessageBox.warning(self, "Lỗi", "Chưa có quy trình (Workflow) nào.")
            return

        raw_vars = self.txt_vars.toPlainText().strip()
        if raw_vars:
            try:
                parsed = json.loads(raw_vars)
                if not isinstance(parsed, dict):
                    raise ValueError("Biến dữ liệu phải là JSON object dạng {...}")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi cú pháp JSON", f"Biến dữ liệu không hợp lệ:\n{e}")
                return

        self.accept()

    def get_data(self):
        raw_vars = self.txt_vars.toPlainText().strip()
        parsed_vars = json.loads(raw_vars) if raw_vars else {}

        sched_cfg = None
        if self.chk_schedule.isChecked():
            iso_str = self.dt_run_at.dateTime().toPython().isoformat()
            sched_cfg = {"run_at": iso_str}

        return {
            "name": self.txt_name.text().strip(),
            "workflow_id": self.cbo_workflow.currentData(),
            "description": self.txt_desc.text().strip(),
            "priority": self.spin_priority.value(),
            "enabled": self.chk_enabled.isChecked(),
            "variables": parsed_vars,
            "schedule_config": sched_cfg,
        }


class MainWindow(QMainWindow):
    """Cửa sổ chính của Smart Web Automation Agent."""

    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self.repo = Repository()
        self.task_manager = TaskManager(repository=self.repo)
        
        # Khởi động TaskScheduler qua SchedulerThread độc lập
        self.scheduler_thread = SchedulerThread(self.task_manager.scheduler)
        self.scheduler_thread.start()

        self.active_worker = None
        self.current_selected_workflow_id = None
        self.current_workflow_def = None

        self.setWindowTitle("Smart Web Automation Agent - Pro Control Center")
        self.resize(1280, 820)
        self.setMinimumSize(1000, 700)
        
        self._setup_style()
        self._init_layout()
        self._seed_sample_data()
        self._load_all_data()

    def closeEvent(self, event):
        """Dừng scheduler thread khi đóng ứng dụng."""
        if hasattr(self, "scheduler_thread") and self.scheduler_thread.isRunning():
            self.scheduler_thread.stop()
        event.accept()

    def _setup_style(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #0f172a; }
            QWidget#sidebar { background-color: #1e293b; border-right: 1px solid #334155; }
            QLabel#sidebar-title { color: #38bdf8; font-size: 16px; font-weight: bold; padding: 14px 10px; }
            
            QPushButton#nav-btn {
                text-align: left;
                padding: 12px 18px;
                background-color: transparent;
                color: #94a3b8;
                font-size: 14px;
                font-weight: 500;
                border: none;
                border-radius: 6px;
                margin: 3px 10px;
            }
            QPushButton#nav-btn:hover { background-color: #334155; color: #f8fafc; }
            QPushButton#nav-btn[active="true"] { background-color: #0284c7; color: white; font-weight: bold; }

            QWidget#content-area { background-color: #0f172a; padding: 15px; }
            
            QFrame.card {
                background-color: #1e293b;
                border-radius: 8px;
                border: 1px solid #334155;
                padding: 16px;
            }
            
            QLabel.heading { color: #f8fafc; font-size: 18px; font-weight: bold; }
            QLabel.subheading { color: #94a3b8; font-size: 13px; margin-bottom: 10px; }
            
            QPushButton.btn-primary {
                background-color: #0284c7;
                color: white;
                font-size: 13px;
                font-weight: bold;
                border-radius: 6px;
                padding: 8px 16px;
                border: none;
            }
            QPushButton.btn-primary:hover { background-color: #0369a1; }
            
            QPushButton.btn-success {
                background-color: #16a34a;
                color: white;
                font-size: 13px;
                font-weight: bold;
                border-radius: 6px;
                padding: 8px 16px;
                border: none;
            }
            QPushButton.btn-success:hover { background-color: #15803d; }

            QPushButton.btn-warning {
                background-color: #d97706;
                color: white;
                font-size: 13px;
                font-weight: bold;
                border-radius: 6px;
                padding: 8px 16px;
                border: none;
            }
            QPushButton.btn-warning:hover { background-color: #b45309; }

            QPushButton.btn-danger {
                background-color: #dc2626;
                color: white;
                font-size: 13px;
                font-weight: bold;
                border-radius: 6px;
                padding: 8px 16px;
                border: none;
            }
            QPushButton.btn-danger:hover { background-color: #b91c1c; }

            QPushButton.btn-secondary {
                background-color: #475569;
                color: #f8fafc;
                font-size: 13px;
                font-weight: 500;
                border-radius: 6px;
                padding: 8px 14px;
                border: none;
            }
            QPushButton.btn-secondary:hover { background-color: #334155; }

            QTableWidget {
                background-color: #1e293b;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 6px;
                gridline-color: #334155;
                selection-background-color: #0284c7;
                selection-color: white;
            }
            QHeaderView::section {
                background-color: #334155;
                color: #e2e8f0;
                font-weight: bold;
                padding: 8px;
                border: none;
            }

            QTextEdit, QLineEdit, QDateTimeEdit {
                background-color: #0b1120;
                color: #38bdf8;
                font-family: Consolas, monospace;
                font-size: 12px;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px;
            }
        """)

    def _init_layout(self):
        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 1. Sidebar bên trái
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(0, 10, 0, 10)

        title = QLabel("🤖 SMART AGENT")
        title.setObjectName("sidebar-title")
        title.setAlignment(Qt.AlignCenter)
        side_layout.addWidget(title)

        self.nav_buttons = []
        self.btn_nav_dashboard = self._add_nav_btn("📊 Bảng Điều Khiển", 0, side_layout)
        self.btn_nav_tasks = self._add_nav_btn("📋 Quản Lý Nhiệm Vụ", 1, side_layout)
        self.btn_nav_builder = self._add_nav_btn("🛠️ Trình Tạo Kịch Bản", 2, side_layout)
        self.btn_nav_monitor = self._add_nav_btn("🖥️ Giám Sát Realtime", 3, side_layout)
        self.btn_nav_settings = self._add_nav_btn("⚙️ Cài Đặt Hệ Thống", 4, side_layout)

        side_layout.addStretch()

        status_box = QFrame()
        status_box.setStyleSheet("background-color: #0f172a; margin: 10px; border-radius: 6px; padding: 10px;")
        box_layout = QVBoxLayout(status_box)
        self.lbl_system_status = QLabel("🟢 Sẵn Sàng (Scheduler Active)")
        self.lbl_system_status.setStyleSheet("color: #4ade80; font-weight: bold; font-size: 12px;")
        box_layout.addWidget(self.lbl_system_status)
        side_layout.addWidget(status_box)

        layout.addWidget(sidebar)

        # 2. Content Area bên phải
        self.stack = QStackedWidget()
        self.stack.setObjectName("content-area")

        self.stack.addWidget(self._build_dashboard_view())
        self.stack.addWidget(self._build_task_view())
        self.stack.addWidget(self._build_workflow_builder_view())
        self.stack.addWidget(self._build_monitor_view())
        self.stack.addWidget(self._build_settings_view())

        layout.addWidget(self.stack)
        self._switch_view(0)

    def _add_nav_btn(self, text, index, layout):
        btn = QPushButton(text)
        btn.setObjectName("nav-btn")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda: self._switch_view(index))
        layout.addWidget(btn)
        self.nav_buttons.append(btn)
        return btn

    def _switch_view(self, index):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setProperty("active", "true" if i == index else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    # ---------------- VIEW 1: DASHBOARD ----------------
    def _build_dashboard_view(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        banner = QFrame()
        banner.setProperty("class", "card")
        b_layout = QVBoxLayout(banner)
        b_title = QLabel("👋 Chào mừng bạn đến với Smart Web Automation Agent!")
        b_title.setStyleSheet("color: #38bdf8; font-size: 16px; font-weight: bold;")
        b_desc = QLabel(
            "Quy trình sử dụng:\n"
            "• Bước 1: Sang 'Trình Tạo Kịch Bản' để cấu hình các bước tự động hóa (Mở trang, Điền form, Nhấp chuột, Chụp ảnh).\n"
            "• Bước 2: Vào 'Quản Lý Nhiệm Vụ' để cấu hình Biến Dữ Liệu (URL, thông tin điền), Đặt lịch chạy hoặc Chạy thử Dry-run.\n"
            "• Bước 3: Xem Chromium thao tác và ảnh chụp màn hình chứng từ tại 'Giám Sát Realtime'."
        )
        b_desc.setStyleSheet("color: #cbd5e1; font-size: 13px; line-height: 150%;")
        b_layout.addWidget(b_title)
        b_layout.addWidget(b_desc)
        layout.addWidget(banner)

        stats_layout = QHBoxLayout()
        self.card_total = self._create_stat_card("Tổng Nhiệm Vụ", "0", "#38bdf8")
        self.card_active = self._create_stat_card("Đang Kích Hoạt", "0", "#4ade80")
        self.card_executions = self._create_stat_card("Lượt Chạy Thành Công", "0", "#a855f7")
        stats_layout.addWidget(self.card_total)
        stats_layout.addWidget(self.card_active)
        stats_layout.addWidget(self.card_executions)
        layout.addLayout(stats_layout)

        actions_box = QHBoxLayout()
        btn_quick_demo = QPushButton("🚀 Chạy Nhanh Demo Trình Duyệt")
        btn_quick_demo.setProperty("class", "btn-primary")
        btn_quick_demo.clicked.connect(self._run_quick_demo)

        btn_go_tasks = QPushButton("➕ Tạo Nhiệm Vụ Mới")
        btn_go_tasks.setProperty("class", "btn-success")
        btn_go_tasks.clicked.connect(self._open_create_task_modal)

        actions_box.addWidget(btn_quick_demo)
        actions_box.addWidget(btn_go_tasks)
        actions_box.addStretch()
        layout.addLayout(actions_box)

        layout.addWidget(QLabel("🕒 Hoạt động gần đây:"))
        self.table_recent_exec = QTableWidget(0, 4)
        self.table_recent_exec.setHorizontalHeaderLabels(["Nhiệm vụ", "Trạng thái", "Bắt đầu", "Ghi chú"])
        self.table_recent_exec.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_recent_exec)

        return widget

    def _create_stat_card(self, title, val, color):
        card = QFrame()
        card.setProperty("class", "card")
        layout = QVBoxLayout(card)
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #94a3b8; font-size: 13px;")
        lbl_val = QLabel(val)
        lbl_val.setStyleSheet(f"color: {color}; font-size: 26px; font-weight: bold;")
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_val)
        return card

    # ---------------- VIEW 2: TASK MANAGER ----------------
    def _build_task_view(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        header = QLabel("Danh Sách Nhiệm Vụ Tự Động Hóa")
        header.setProperty("class", "heading")
        sub = QLabel("Kích hoạt, cấu hình biến dữ liệu, đặt lịch hoặc chạy thử an toàn (Dry-run).")
        sub.setProperty("class", "subheading")
        layout.addWidget(header)
        layout.addWidget(sub)

        toolbar = QHBoxLayout()
        btn_add = QPushButton("➕ Thêm Nhiệm Vụ Mới")
        btn_add.setProperty("class", "btn-success")
        btn_add.clicked.connect(self._open_create_task_modal)

        btn_vars = QPushButton("⚙️ Cấu Hình Biến Cho Task")
        btn_vars.setProperty("class", "btn-secondary")
        btn_vars.clicked.connect(self._open_edit_task_vars)

        self.btn_dry_run = QPushButton("🛡️ Chạy Thử An Toàn (Dry-run)")
        self.btn_dry_run.setProperty("class", "btn-warning")
        self.btn_dry_run.clicked.connect(lambda: self._execute_selected_task(dry_run=True))

        self.btn_run = QPushButton("▶ Chạy Thật Trên Trình Duyệt")
        self.btn_run.setProperty("class", "btn-primary")
        self.btn_run.clicked.connect(lambda: self._execute_selected_task(dry_run=False))

        btn_refresh = QPushButton("🔄 Làm Mới")
        btn_refresh.setProperty("class", "btn-secondary")
        btn_refresh.clicked.connect(self._load_tasks_table)

        toolbar.addWidget(btn_add)
        toolbar.addWidget(btn_vars)
        toolbar.addWidget(self.btn_dry_run)
        toolbar.addWidget(self.btn_run)
        toolbar.addWidget(btn_refresh)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.table_tasks = QTableWidget(0, 7)
        self.table_tasks.setHorizontalHeaderLabels(["ID", "Tên nhiệm vụ", "Độ ưu tiên", "Trạng thái", "Lịch chạy", "Biến số", "Thao tác"])
        self.table_tasks.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_tasks.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table_tasks)

        return widget

    # ---------------- VIEW 3: TRÌNH TẠO KỊCH BẢN (WORKFLOW BUILDER) ----------------
    def _build_workflow_builder_view(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        header = QLabel("Trình Xây Dựng & Quản Lý Kịch Bản (Workflow Builder)")
        header.setProperty("class", "heading")
        sub = QLabel("Thêm, sửa, xóa hoặc cấu hình trực quan từng bước thao tác (Mở trang, Điền form, Nhấp chuột, Chờ đợi).")
        sub.setProperty("class", "subheading")
        layout.addWidget(header)
        layout.addWidget(sub)

        wf_selector_box = QHBoxLayout()
        wf_selector_box.addWidget(QLabel("<b>Đang chọn kịch bản:</b>"))
        self.cbo_active_wf = QComboBox()
        self.cbo_active_wf.currentIndexChanged.connect(self._on_active_workflow_changed)
        wf_selector_box.addWidget(self.cbo_active_wf, 1)

        btn_new_wf = QPushButton("➕ Tạo Kịch Bản Mới")
        btn_new_wf.setProperty("class", "btn-success")
        btn_new_wf.clicked.connect(self._create_new_workflow)
        wf_selector_box.addWidget(btn_new_wf)

        layout.addLayout(wf_selector_box)

        splitter = QSplitter(Qt.Horizontal)

        left_box = QFrame()
        left_box.setProperty("class", "card")
        l_layout = QVBoxLayout(left_box)

        l_toolbar = QHBoxLayout()
        l_toolbar.addWidget(QLabel("<b>Các bước thao tác trong kịch bản:</b>"))
        l_toolbar.addStretch()

        btn_add_step = QPushButton("➕ Thêm Thao Tác Mới")
        btn_add_step.setProperty("class", "btn-primary")
        btn_add_step.clicked.connect(self._open_add_step_dialog)
        l_toolbar.addWidget(btn_add_step)

        btn_edit_step = QPushButton("✏️ Sửa Bước")
        btn_edit_step.setProperty("class", "btn-secondary")
        btn_edit_step.clicked.connect(self._open_edit_step_dialog)
        l_toolbar.addWidget(btn_edit_step)

        btn_del_step = QPushButton("🗑️ Xóa Bước")
        btn_del_step.setProperty("class", "btn-danger")
        btn_del_step.clicked.connect(self._delete_selected_step)
        l_toolbar.addWidget(btn_del_step)

        l_layout.addLayout(l_toolbar)

        self.table_steps = QTableWidget(0, 5)
        self.table_steps.setHorizontalHeaderLabels(["Thứ tự", "Mã bước", "Hành động", "Rủi ro", "Mô tả / Tham số"])
        self.table_steps.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_steps.setSelectionBehavior(QTableWidget.SelectRows)
        l_layout.addWidget(self.table_steps)

        splitter.addWidget(left_box)

        right_box = QFrame()
        right_box.setProperty("class", "card")
        right_box.setFixedWidth(420)
        r_layout = QVBoxLayout(right_box)
        r_layout.addWidget(QLabel("<b>Cấu hình YAML tương ứng:</b>"))
        self.txt_workflow_yaml = QTextEdit()
        r_layout.addWidget(self.txt_workflow_yaml)

        btn_apply_yaml = QPushButton("💾 Cập Nhật Từ YAML")
        btn_apply_yaml.setProperty("class", "btn-primary")
        btn_apply_yaml.clicked.connect(self._save_from_yaml_editor)
        r_layout.addWidget(btn_apply_yaml)

        splitter.addWidget(right_box)
        layout.addWidget(splitter)

        return widget

    # ---------------- VIEW 4: LIVE MONITOR ----------------
    def _build_monitor_view(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        header = QLabel("Giám Sát Thời Gian Thực (Live Monitor)")
        header.setProperty("class", "heading")
        sub = QLabel("Theo dõi Chromium tự động điều khiển, xem log chi tiết và ảnh chụp màn hình chứng từ.")
        sub.setProperty("class", "subheading")
        layout.addWidget(header)
        layout.addWidget(sub)

        splitter = QSplitter(Qt.Horizontal)

        left_panel = QFrame()
        left_panel.setProperty("class", "card")
        l_layout = QVBoxLayout(left_panel)
        l_layout.addWidget(QLabel("<b>Nhật ký thực thi hệ thống (Live Logs):</b>"))
        self.txt_monitor_logs = QTextEdit()
        self.txt_monitor_logs.setReadOnly(True)
        l_layout.addWidget(self.txt_monitor_logs)
        splitter.addWidget(left_panel)

        right_panel = QFrame()
        right_panel.setProperty("class", "card")
        r_layout = QVBoxLayout(right_panel)
        r_layout.addWidget(QLabel("<b>Ảnh chụp màn hình mới nhất:</b>"))
        self.lbl_latest_screenshot = QLabel("Chưa có ảnh chụp mới.")
        self.lbl_latest_screenshot.setAlignment(Qt.AlignCenter)
        self.lbl_latest_screenshot.setStyleSheet("background-color: #0b1120; border-radius: 6px; color: #64748b;")
        self.lbl_latest_screenshot.setMinimumSize(420, 280)
        r_layout.addWidget(self.lbl_latest_screenshot)
        splitter.addWidget(right_panel)

        layout.addWidget(splitter)

        self.timer_monitor = QTimer(self)
        self.timer_monitor.timeout.connect(self._refresh_monitor_content)
        self.timer_monitor.start(1500)

        return widget

    # ---------------- VIEW 5: SETTINGS ----------------
    def _build_settings_view(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        header = QLabel("Cài Đặt Hệ Thống")
        header.setProperty("class", "heading")
        sub = QLabel("Thông số môi trường hoạt động và cấu hình Chromium.")
        sub.setProperty("class", "subheading")
        layout.addWidget(header)
        layout.addWidget(sub)

        card = QFrame()
        card.setProperty("class", "card")
        form = QFormLayout(card)

        form.addRow("Thư mục dự án:", QLabel(str(self.settings.BASE_DIR)))
        form.addRow("Đường dẫn SQLite DB:", QLabel(str(self.settings.DATA_DIR / "autoweb.db")))
        form.addRow("Trình duyệt mặc định:", QLabel(f"{self.settings.BROWSER_TYPE.upper()} (Chromium)"))
        form.addRow("Độ trễ thao tác (Slow-mo):", QLabel(f"{self.settings.SLOW_MO_MS} ms"))
        form.addRow("Thời gian chờ (Timeout):", QLabel(f"{self.settings.DEFAULT_TIMEOUT_MS} ms"))
        form.addRow("Thư mục lưu ảnh lỗi/chứng từ:", QLabel(str(self.settings.SCREENSHOTS_DIR)))
        form.addRow("Thư mục lưu phiên (Profiles):", QLabel(str(self.settings.PROFILES_DIR)))

        layout.addWidget(card)
        layout.addStretch()
        return widget

    # ---------------- LOGIC XỬ LÝ ----------------
    def _seed_sample_data(self):
        wfs = self.repo.list_workflows()
        if not wfs:
            yaml_path = self.settings.BASE_DIR / "workflows" / "course_registration.yaml"
            if yaml_path.exists():
                wf_def = WorkflowDefinition.from_yaml(yaml_path.read_text(encoding="utf-8"))
                wf_model = self.repo.save_workflow(wf_def)
                self.repo.create_task(
                    name="Đăng ký học phần thử nghiệm",
                    workflow_id=wf_model.id,
                    description="Mô phỏng quy trình mở cổng, nhập tên, mã môn học và submit an toàn.",
                    priority=2,
                    variables={
                        "portal_url": (self.settings.BASE_DIR / "tests" / "fixtures" / "test_page.html").as_uri(),
                        "student_name": "Nguyễn Văn A",
                        "course_code": "CS101-AUTOMATION",
                    }
                )

    def _load_all_data(self):
        self._load_tasks_table()
        self._load_workflow_dropdown()
        self._update_dashboard_stats()

    def _update_dashboard_stats(self):
        tasks = self.task_manager.list_tasks()
        active_count = sum(1 for t in tasks if t.enabled)
        
        self.card_total.findChildren(QLabel)[1].setText(str(len(tasks)))
        self.card_active.findChildren(QLabel)[1].setText(str(active_count))

        self.table_recent_exec.setRowCount(min(len(tasks), 5))
        for i, t in enumerate(tasks[:5]):
            self.table_recent_exec.setItem(i, 0, QTableWidgetItem(t.name))
            self.table_recent_exec.setItem(i, 1, QTableWidgetItem("Sẵn sàng" if t.enabled else "Đã tắt"))
            self.table_recent_exec.setItem(i, 2, QTableWidgetItem(datetime.now().strftime("%H:%M:%S")))
            self.table_recent_exec.setItem(i, 3, QTableWidgetItem("Hệ thống cục bộ ổn định"))

    def _load_tasks_table(self):
        tasks = self.task_manager.list_tasks()
        self.table_tasks.setRowCount(len(tasks))

        for i, t in enumerate(tasks):
            self.table_tasks.setItem(i, 0, QTableWidgetItem(t.id[:8]))
            self.table_tasks.item(i, 0).setData(Qt.UserRole, t.id)
            self.table_tasks.setItem(i, 1, QTableWidgetItem(t.name))
            self.table_tasks.setItem(i, 2, QTableWidgetItem(f"Ưu tiên {t.priority}"))
            self.table_tasks.setItem(i, 3, QTableWidgetItem("🟢 Bật" if t.enabled else "⚪ Tắt"))
            
            sched_str = "Thủ công"
            if t.schedule_config:
                try:
                    c = json.loads(t.schedule_config)
                    sched_str = c.get("run_at", str(c))
                except Exception:
                    pass
            self.table_tasks.setItem(i, 4, QTableWidgetItem(sched_str))

            vars_count = 0
            if t.variables_json:
                try:
                    vars_count = len(json.loads(t.variables_json))
                except Exception:
                    pass
            self.table_tasks.setItem(i, 5, QTableWidgetItem(f"{vars_count} biến"))

            btn_toggle = QPushButton("Đổi Trạng Thái")
            btn_toggle.setProperty("class", "btn-secondary")
            btn_toggle.clicked.connect(lambda checked, tid=t.id: self._toggle_task(tid))
            self.table_tasks.setCellWidget(i, 6, btn_toggle)

    def _open_edit_task_vars(self):
        curr_row = self.table_tasks.currentRow()
        if curr_row < 0:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn một nhiệm vụ trong danh sách để xem/sửa biến.")
            return

        task_id = self.table_tasks.item(curr_row, 0).data(Qt.UserRole)
        task = self.task_manager.get_task(task_id)
        if not task:
            return

        current_vars = {}
        if task.variables_json:
            try:
                current_vars = json.loads(task.variables_json)
            except Exception:
                pass

        dlg = TaskVariablesDialog(self, task_name=task.name, current_vars=current_vars)
        if dlg.exec() == QDialog.Accepted:
            new_vars = dlg.get_variables()
            self.task_manager.update_variables(task_id, new_vars)
            self._load_tasks_table()
            QMessageBox.information(self, "Thành công", f"Đã cập nhật biến dữ liệu cho nhiệm vụ '{task.name}'!")

    def _load_workflow_dropdown(self):
        self.cbo_active_wf.blockSignals(True)
        self.cbo_active_wf.clear()
        wfs = self.repo.list_workflows()
        for wf in wfs:
            self.cbo_active_wf.addItem(f"{wf.name} (v{wf.version})", wf.id)
        self.cbo_active_wf.blockSignals(False)

        if wfs:
            self.cbo_active_wf.setCurrentIndex(0)
            self._on_active_workflow_changed(0)

    def _on_active_workflow_changed(self, index):
        if index < 0 or self.cbo_active_wf.count() == 0:
            return
        wf_id = self.cbo_active_wf.currentData()
        self.current_selected_workflow_id = wf_id
        wf = self.repo.get_workflow(wf_id)
        if wf:
            try:
                data = json.loads(wf.definition_json)
                self.current_workflow_def = WorkflowDefinition(**data)
                self.txt_workflow_yaml.setPlainText(self.current_workflow_def.to_yaml())
                self._render_steps_table()
            except Exception as e:
                logger.error(f"Lỗi đọc kịch bản: {e}")

    def _render_steps_table(self):
        if not self.current_workflow_def:
            self.table_steps.setRowCount(0)
            return

        steps = self.current_workflow_def.steps
        self.table_steps.setRowCount(len(steps))
        for i, s in enumerate(steps):
            self.table_steps.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.table_steps.setItem(i, 1, QTableWidgetItem(s.id))
            self.table_steps.item(i, 1).setData(Qt.UserRole, i)
            self.table_steps.setItem(i, 2, QTableWidgetItem(s.action))
            self.table_steps.setItem(i, 3, QTableWidgetItem(s.risk_level.value.upper()))
            
            summary = s.description or str(s.params)
            self.table_steps.setItem(i, 4, QTableWidgetItem(summary))

    def _open_add_step_dialog(self):
        if not self.current_workflow_def:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn hoặc tạo kịch bản trước.")
            return

        dlg = StepEditorDialog(self)
        if dlg.exec() == QDialog.Accepted:
            new_step = dlg.get_step()
            self.current_workflow_def.steps.append(new_step)
            self._save_active_workflow_def()

    def _open_edit_step_dialog(self):
        curr_row = self.table_steps.currentRow()
        if curr_row < 0:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn một bước trong bảng để sửa.")
            return

        step_idx = self.table_steps.item(curr_row, 1).data(Qt.UserRole)
        step = self.current_workflow_def.steps[step_idx]

        dlg = StepEditorDialog(self, step_data=step)
        if dlg.exec() == QDialog.Accepted:
            updated_step = dlg.get_step()
            self.current_workflow_def.steps[step_idx] = updated_step
            self._save_active_workflow_def()

    def _delete_selected_step(self):
        curr_row = self.table_steps.currentRow()
        if curr_row < 0:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn một bước trong bảng để xóa.")
            return

        step_idx = self.table_steps.item(curr_row, 1).data(Qt.UserRole)
        step_name = self.current_workflow_def.steps[step_idx].id

        if QMessageBox.question(self, "Xác nhận xóa", f"Bạn có chắc muốn xóa bước '{step_name}'?") == QMessageBox.Yes:
            self.current_workflow_def.steps.pop(step_idx)
            self._save_active_workflow_def()

    def _save_active_workflow_def(self):
        if self.current_selected_workflow_id and self.current_workflow_def:
            self.repo.save_workflow(self.current_workflow_def, workflow_id=self.current_selected_workflow_id)
            self.txt_workflow_yaml.setPlainText(self.current_workflow_def.to_yaml())
            self._render_steps_table()
            QMessageBox.information(self, "Thành công", "Đã lưu kịch bản và cập nhật các bước thành công!")

    def _save_from_yaml_editor(self):
        if not self.current_selected_workflow_id:
            return
        yaml_text = self.txt_workflow_yaml.toPlainText()
        try:
            wf_def = WorkflowDefinition.from_yaml(yaml_text)
            self.current_workflow_def = wf_def
            self.repo.save_workflow(wf_def, workflow_id=self.current_selected_workflow_id)
            self._render_steps_table()
            QMessageBox.information(self, "Thành công", "Đã đồng bộ nội dung từ YAML vào kịch bản!")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi cú pháp", f"Không thể lưu do lỗi YAML:\n{e}")

    def _create_new_workflow(self):
        new_name, ok = QInputDialog.getText(self, "Tạo Kịch Bản Mới", "Nhập tên kịch bản mới:")
        if ok and new_name.strip():
            new_wf = WorkflowDefinition(
                name=new_name.strip(),
                steps=[
                    WorkflowStep(
                        id="open_homepage",
                        action="navigate",
                        description="Mở trang web",
                        params={"url": "https://example.com", "wait_until": "domcontentloaded"},
                    )
                ]
            )
            model = self.repo.save_workflow(new_wf)
            self._load_workflow_dropdown()
            for i in range(self.cbo_active_wf.count()):
                if self.cbo_active_wf.itemData(i) == model.id:
                    self.cbo_active_wf.setCurrentIndex(i)
                    break

    def _toggle_task(self, task_id):
        self.task_manager.toggle_task(task_id)
        self._load_tasks_table()
        self._update_dashboard_stats()

    def _open_create_task_modal(self):
        wfs = self.repo.list_workflows()
        dlg = CreateTaskDialog(self, workflows=wfs)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            self.task_manager.create_task(
                name=data["name"],
                workflow_id=data["workflow_id"],
                description=data["description"],
                priority=data["priority"],
                variables=data.get("variables"),
                schedule_config=data.get("schedule_config"),
            )
            self._load_all_data()
            self._switch_view(1)
            QMessageBox.information(self, "Thành công", f"Đã tạo nhiệm vụ '{data['name']}' thành công!")

    def _execute_selected_task(self, dry_run=False):
        curr_row = self.table_tasks.currentRow()
        if curr_row < 0:
            QMessageBox.warning(self, "Chưa chọn nhiệm vụ", "Vui lòng chọn một dòng nhiệm vụ trong danh sách để chạy.")
            return

        task_id = self.table_tasks.item(curr_row, 0).data(Qt.UserRole)
        task_name = self.table_tasks.item(curr_row, 1).text()

        mode_str = "CHẾ ĐỘ AN TOÀN (Dry-run)" if dry_run else "CHẾ ĐỘ THỰC THI THẬT"
        msg = f"Kích hoạt '{task_name}' ở {mode_str}?\n\nTrình duyệt Chromium sẽ tự động mở lên màn hình."
        
        reply = QMessageBox.question(self, "Xác nhận chạy", msg, QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self._switch_view(3)
            self.lbl_system_status.setText("🟡 Đang Chạy...")
            self.lbl_system_status.setStyleSheet("color: #facc15; font-weight: bold; font-size: 13px;")

            self.active_worker = TaskExecutionWorker(self.task_manager, task_id=task_id, dry_run=dry_run)
            self.active_worker.finished_signal.connect(self._on_task_finished)
            self.active_worker.error_signal.connect(self._on_task_error)
            self.active_worker.start()

    def _on_task_finished(self, result):
        self.lbl_system_status.setText("🟢 Sẵn Sàng (Scheduler Active)")
        self.lbl_system_status.setStyleSheet("color: #4ade80; font-weight: bold; font-size: 13px;")
        self._load_all_data()
        status = result.get("status", "SUCCESS")
        QMessageBox.information(self, "Hoàn thành", f"Lượt chạy kịch bản kết thúc với kết quả: {status}")

    def _on_task_error(self, err_msg):
        self.lbl_system_status.setText("🔴 Lỗi")
        self.lbl_system_status.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 13px;")
        QMessageBox.critical(self, "Lỗi thực thi", f"Đã xảy ra lỗi trong quá trình chạy:\n{err_msg}")

    def _run_quick_demo(self):
        self._switch_view(3)
        self.lbl_system_status.setText("🟡 Đang Chạy Demo...")
        self.lbl_system_status.setStyleSheet("color: #facc15; font-weight: bold; font-size: 13px;")
        
        tasks = self.task_manager.list_tasks()
        if tasks:
            self.active_worker = TaskExecutionWorker(self.task_manager, task_id=tasks[0].id, dry_run=False)
            self.active_worker.finished_signal.connect(self._on_task_finished)
            self.active_worker.error_signal.connect(self._on_task_error)
            self.active_worker.start()
        else:
            from demo_phase1 import run_demo
            import asyncio
            asyncio.run(run_demo())
            self.lbl_system_status.setText("🟢 Sẵn Sàng (Scheduler Active)")
            self.lbl_system_status.setStyleSheet("color: #4ade80; font-weight: bold; font-size: 13px;")
            QMessageBox.information(self, "Demo hoàn tất", "Kịch bản Demo đã chạy xong!")

    def _refresh_monitor_content(self):
        log_file = self.settings.LOGS_DIR / self.settings.LOG_FILE_NAME
        if log_file.exists():
            try:
                content = log_file.read_text(encoding="utf-8", errors="replace")
                lines = content.splitlines()[-60:]
                self.txt_monitor_logs.setPlainText("\n".join(lines))
                self.txt_monitor_logs.verticalScrollBar().setValue(
                    self.txt_monitor_logs.verticalScrollBar().maximum()
                )
            except Exception:
                pass

        shots = list(self.settings.SCREENSHOTS_DIR.glob("*.png"))
        if shots:
            latest_shot = max(shots, key=lambda f: f.stat().st_mtime)
            pixmap = QPixmap(str(latest_shot))
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    self.lbl_latest_screenshot.width() - 10,
                    self.lbl_latest_screenshot.height() - 10,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                self.lbl_latest_screenshot.setPixmap(scaled)


def run_app():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_app()
