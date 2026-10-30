"""Hộp thoại hướng dẫn và kích hoạt Ghi Thao Tác Trực Tiếp (Web Recorder)."""

from pathlib import Path
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QMessageBox,
    QFrame,
    QProgressBar,
)
from PySide6.QtCore import Qt

from app.config import get_settings
from app.ui.recorder_worker import RecorderWorker
from app.core.workflow_recorder import WorkflowRecorder
from app.core.workflow_models import WorkflowDefinition


class RecordWorkflowDialog(QDialog):
    """Hộp thoại ghi thao tác người dùng bằng Playwright Codegen."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔴 Ghi Thao Tác Trực Tiếp (Smart Web Recorder)")
        self.resize(580, 420)
        self.settings = get_settings()
        self.worker = None
        self.generated_workflow: WorkflowDefinition = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Hộp hướng dẫn thân thiện
        guide_frame = QFrame()
        guide_frame.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border: 1px solid #38bdf8;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        guide_layout = QVBoxLayout(guide_frame)
        title = QLabel("💡 HƯỚNG DẪN GHI THAO TÁC CỰC KỲ ĐƠN GIẢN:")
        title.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 13px;")
        guide_layout.addWidget(title)

        steps_text = QLabel(
            "1. Nhập URL trang web bạn muốn tự động hóa.\n"
            "2. Bấm 'Bắt Đầu Ghi Thao Tác' -> Cửa sổ trình duyệt sẽ tự động mở lên.\n"
            "3. Bạn chỉ cần dùng chuột click, gõ bàn phím lướt web như bình thường.\n"
            "4. Khi hoàn thành, chỉ cần ĐÓNG CỬA SỔ TRÌNH DUYỆT.\n"
            "5. Toàn bộ thao tác sẽ tự động chuyển thành kịch bản hoàn chỉnh!"
        )
        steps_text.setStyleSheet("color: #cbd5e1; font-size: 12px; line-height: 1.4;")
        guide_layout.addWidget(steps_text)
        layout.addWidget(guide_frame)

        # Form nhập liệu
        form = QFormLayout()
        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("VD: Đăng nhập Facebook, Săn vé xem phim...")
        self.txt_name.setText("Kịch bản ghi nhận mới")
        form.addRow("Tên kịch bản (*):", self.txt_name)

        self.txt_url = QLineEdit()
        self.txt_url.setPlaceholderText("https://example.com hoặc để trống")
        self.txt_url.setText("https://")
        form.addRow("Địa chỉ trang web (URL):", self.txt_url)

        layout.addLayout(form)

        # Trạng thái tiến trình
        self.status_label = QLabel("Trạng thái: Sẵn sàng")
        self.status_label.setStyleSheet("color: #94a3b8; font-size: 12px; font-style: italic;")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Nút bấm hành động
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        self.btn_cancel = QPushButton("Hủy bỏ")
        self.btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(self.btn_cancel)

        self.btn_start = QPushButton("🔴 Bắt Đầu Ghi Thao Tác")
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #dc2626;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #b91c1c;
            }
        """)
        self.btn_start.clicked.connect(self._start_recording)
        btn_box.addWidget(self.btn_start)

        layout.addLayout(btn_box)

    def _start_recording(self):
        wf_name = self.txt_name.text().strip()
        if not wf_name:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập tên kịch bản.")
            return

        raw_url = self.txt_url.text().strip()
        if raw_url == "https://" or not raw_url:
            raw_url = "about:blank"

        temp_script_path = self.settings.DATA_DIR / "temp_recorded_script.py"

        self.btn_start.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        self.txt_name.setEnabled(False)
        self.txt_url.setEnabled(False)

        self.status_label.setText("🔴 Đang ghi nhận... Hãy thao tác trên trình duyệt. Đóng trình duyệt khi xong!")
        self.status_label.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 13px;")
        self.progress_bar.setVisible(True)

        self.worker = RecorderWorker(url=raw_url, output_file=temp_script_path)
        self.worker.finished_signal.connect(self._on_recording_finished)
        self.worker.error_signal.connect(self._on_recording_error)
        self.worker.start()

    def _on_recording_finished(self, script_path_str: str):
        self.progress_bar.setVisible(False)
        self.btn_start.setEnabled(True)
        self.btn_cancel.setEnabled(True)

        script_path = Path(script_path_str)
        try:
            content = script_path.read_text(encoding="utf-8", errors="replace")
            wf_name = self.txt_name.text().strip() or "Kịch bản tự động ghi nhận"
            self.generated_workflow = WorkflowRecorder.parse_script(content, workflow_name=wf_name)

            if not self.generated_workflow.steps:
                QMessageBox.warning(self, "Thông báo", "Không ghi nhận được bước thao tác nào.")
                self.reject()
                return

            # Xóa file tạm
            try:
                script_path.unlink()
            except Exception:
                pass

            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi phân tích", f"Lỗi khi chuyển đổi kịch bản: {e}")
            self.reject()

    def _on_recording_error(self, err_msg: str):
        self.progress_bar.setVisible(False)
        self.btn_start.setEnabled(True)
        self.btn_cancel.setEnabled(True)
        self.txt_name.setEnabled(True)
        self.txt_url.setEnabled(True)
        self.status_label.setText("Trạng thái: Đã dừng")
        self.status_label.setStyleSheet("color: #94a3b8;")

        QMessageBox.information(self, "Ghi nhận dừng lại", err_msg)

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
        event.accept()
