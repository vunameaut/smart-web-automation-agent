"""Hộp thoại chọn và áp dụng kịch bản mẫu có sẵn (Workflow Presets)."""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QPushButton,
    QTextEdit,
    QSplitter,
    QFrame,
    QMessageBox,
)
from PySide6.QtCore import Qt

from app.core.workflow_presets import PRESET_WORKFLOWS
from app.core.workflow_models import WorkflowDefinition


class PresetSelectorDialog(QDialog):
    """Hộp thoại danh mục kịch bản mẫu 1-click."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚡ Thư Viện Kịch Bản Mẫu (1-Click Presets)")
        self.resize(750, 480)
        self.selected_workflow: WorkflowDefinition = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        header = QLabel("Chọn một mẫu kịch bản có sẵn để áp dụng ngay mà không cần cấu hình từ đầu:")
        header.setStyleSheet("color: #94a3b8; font-size: 13px; margin-bottom: 5px;")
        layout.addWidget(header)

        splitter = QSplitter(Qt.Horizontal)

        # Danh sách kịch bản mẫu bên trái
        self.list_presets = QListWidget()
        self.list_presets.setStyleSheet("""
            QListWidget {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #f8fafc;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #334155;
            }
            QListWidget::item:selected {
                background-color: #0284c7;
                color: white;
                font-weight: bold;
            }
        """)
        for item in PRESET_WORKFLOWS:
            list_item = QListWidgetItem(item["name"])
            list_item.setData(Qt.UserRole, item)
            self.list_presets.addItem(list_item)
        self.list_presets.currentRowChanged.connect(self._on_preset_selected)
        splitter.addWidget(self.list_presets)

        # Khung chi tiết bên phải
        right_frame = QFrame()
        right_frame.setStyleSheet("background-color: #0f172a; border-radius: 6px; padding: 10px;")
        right_layout = QVBoxLayout(right_frame)

        self.lbl_title = QLabel("Chi tiết kịch bản mẫu")
        self.lbl_title.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 15px;")
        right_layout.addWidget(self.lbl_title)

        self.lbl_desc = QLabel()
        self.lbl_desc.setWordWrap(True)
        self.lbl_desc.setStyleSheet("color: #cbd5e1; font-size: 12px; margin-bottom: 10px;")
        right_layout.addWidget(self.lbl_desc)

        self.txt_preview = QTextEdit()
        self.txt_preview.setReadOnly(True)
        self.txt_preview.setStyleSheet("""
            QTextEdit {
                background-color: #1e293b;
                border: 1px solid #334155;
                color: #a5f3fc;
                font-family: Consolas, monospace;
                font-size: 12px;
            }
        """)
        right_layout.addWidget(self.txt_preview)

        splitter.addWidget(right_frame)
        splitter.setSizes([300, 450])
        layout.addWidget(splitter)

        # Nút bấm
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        btn_cancel = QPushButton("Hủy bỏ")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        self.btn_apply = QPushButton("⚡ Áp Dụng Mẫu Này")
        self.btn_apply.setStyleSheet("""
            QPushButton {
                background-color: #16a34a;
                color: white;
                font-weight: bold;
                padding: 8px 18px;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #15803d;
            }
        """)
        self.btn_apply.clicked.connect(self._apply_preset)
        btn_box.addWidget(self.btn_apply)

        layout.addLayout(btn_box)

        # Chọn dòng đầu tiên mặc định
        if self.list_presets.count() > 0:
            self.list_presets.setCurrentRow(0)

    def _on_preset_selected(self, row):
        if row < 0:
            return
        item = self.list_presets.item(row).data(Qt.UserRole)
        self.lbl_title.setText(item["name"])
        self.lbl_desc.setText(item["description"])
        wf: WorkflowDefinition = item["workflow"]
        self.txt_preview.setPlainText(wf.to_yaml())

    def _apply_preset(self):
        curr_row = self.list_presets.currentRow()
        if curr_row < 0:
            QMessageBox.warning(self, "Chưa chọn mẫu", "Vui lòng chọn một kịch bản mẫu trong danh sách.")
            return

        item = self.list_presets.item(curr_row).data(Qt.UserRole)
        self.selected_workflow = item["workflow"]
        self.accept()
