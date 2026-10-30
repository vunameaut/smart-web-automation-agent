"""Hộp thoại chỉnh sửa biến dữ liệu (Variables) cho Task."""

import json
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QLabel,
    QTextEdit,
)


class TaskVariablesDialog(QDialog):
    """Hộp thoại xem và nhập biến (JSON) cho từng Task."""

    def __init__(self, parent=None, task_name="", current_vars=None):
        super().__init__(parent)
        self.setWindowTitle(f"⚙️ Cấu Hình Biến Dữ Liệu - {task_name}")
        self.resize(500, 380)
        self.current_vars = current_vars or {}
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        info = QLabel(
            "Nhập các biến dạng JSON để truyền vào kịch bản (VD: URL, tài khoản, mật khẩu):\n"
            "Các biến sẽ tự động thay thế cho cú pháp {{tên_biến}} trong kịch bản."
        )
        info.setStyleSheet("color: #94a3b8; font-size: 13px; margin-bottom: 8px;")
        layout.addWidget(info)

        self.txt_json = QTextEdit()
        self.txt_json.setPlaceholderText('{\n  "portal_url": "https://example.com",\n  "student_name": "Nguyễn Văn A"\n}')
        self.txt_json.setPlainText(json.dumps(self.current_vars, indent=2, ensure_ascii=False))
        layout.addWidget(self.txt_json)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_cancel = QPushButton("Hủy bỏ")
        btn_cancel.clicked.connect(self.reject)
        
        btn_save = QPushButton("💾 Lưu Cấu Hình Biến")
        btn_save.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold; padding: 8px 16px;")
        btn_save.clicked.connect(self._validate_and_save)

        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

    def _validate_and_save(self):
        text = self.txt_json.toPlainText().strip()
        if not text:
            self.result_vars = {}
            self.accept()
            return

        try:
            parsed = json.loads(text)
            if not isinstance(parsed, dict):
                raise ValueError("Nội dung phải là một JSON Object { ... }")
            self.result_vars = parsed
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi cú pháp JSON", f"Định dạng JSON không hợp lệ:\n{e}")

    def get_variables(self):
        return getattr(self, "result_vars", {})

