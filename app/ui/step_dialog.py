"""Dialog tạo hoặc chỉnh sửa từng bước thao tác (Step) trong Workflow."""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QPushButton,
    QMessageBox,
    QLabel,
    QGroupBox,
)
from app.core.workflow_models import WorkflowStep, RiskLevel, VerifyCondition, VerifyType


class StepEditorDialog(QDialog):
    """Hộp thoại trực quan để thêm/sửa một bước hành động (Action Step)."""

    def __init__(self, parent=None, step_data=None):
        super().__init__(parent)
        self.setWindowTitle("🛠️ Cấu Hình Thao Tác (Action Step)")
        self.resize(550, 480)
        self.step_data = step_data
        self._init_ui()
        if step_data:
            self._load_existing_data(step_data)

    def _init_ui(self):
        layout = QVBoxLayout(self)

        info = QLabel("Chọn loại thao tác và điền các tham số tương ứng bên dưới:")
        info.setStyleSheet("color: #94a3b8; font-size: 13px; margin-bottom: 8px;")
        layout.addWidget(info)

        form = QFormLayout()

        # 1. Step ID & Description
        self.txt_id = QLineEdit()
        self.txt_id.setPlaceholderText("VD: step_click_login, step_fill_code...")
        form.addRow("Mã bước (ID) (*):", self.txt_id)

        self.txt_desc = QLineEdit()
        self.txt_desc.setPlaceholderText("VD: Nhấp vào nút Đăng nhập...")
        form.addRow("Mô tả bước:", self.txt_desc)

        # 2. Loại Action
        self.cbo_action = QComboBox()
        self.cbo_action.addItems([
            "navigate (Mở URL)",
            "click (Nhấp chuột)",
            "fill (Nhập dữ liệu)",
            "wait_for (Chờ phần tử hiển thị)",
            "read_text (Đọc nội dung văn bản)",
            "screenshot (Chụp ảnh màn hình)",
            "wait (Dừng chờ vài giây)",
        ])
        self.cbo_action.currentIndexChanged.connect(self._on_action_changed)
        form.addRow("Loại hành động (*):", self.cbo_action)

        # 3. Mức độ rủi ro (Risk Level)
        self.cbo_risk = QComboBox()
        self.cbo_risk.addItem("LOW (An toàn / Đọc dữ liệu)", "low")
        self.cbo_risk.addItem("MEDIUM (Tương tác form tạm thời)", "medium")
        self.cbo_risk.addItem("HIGH (Gửi đơn / Đặt hàng - Dry Run sẽ bỏ qua)", "high")
        self.cbo_risk.addItem("CRITICAL (Thanh toán / Ràng buộc tài chính)", "critical")
        form.addRow("Mức độ rủi ro:", self.cbo_risk)

        layout.addLayout(form)

        # 4. Box tham số động tùy theo action
        self.param_box = QGroupBox("Tham Số Hành Động")
        self.param_layout = QFormLayout(self.param_box)

        # Param fields
        self.txt_url = QLineEdit()
        self.txt_url.setPlaceholderText("https://... hoặc {{url_bien}}")
        self.param_layout.addRow("URL cần mở:", self.txt_url)

        self.cbo_loc_type = QComboBox()
        self.cbo_loc_type.addItems(["role + name", "label", "placeholder", "text", "css"])
        self.txt_loc_val = QLineEdit()
        self.txt_loc_val.setPlaceholderText("Giá trị tìm kiếm (VD: Đăng ký / Username / CS101)")
        loc_row = QHBoxLayout()
        loc_row.addWidget(self.cbo_loc_type)
        loc_row.addWidget(self.txt_loc_val)
        self.param_layout.addRow("Định vị phần tử:", loc_row)

        self.txt_fill_value = QLineEdit()
        self.txt_fill_value.setPlaceholderText("Dữ liệu cần nhập hoặc {{bien_du_lieu}}")
        self.param_layout.addRow("Giá trị nhập vào:", self.txt_fill_value)

        self.spin_wait_sec = QSpinBox()
        self.spin_wait_sec.setRange(1, 60)
        self.spin_wait_sec.setValue(2)
        self.param_layout.addRow("Số giây cần dừng:", self.spin_wait_sec)

        layout.addWidget(self.param_box)

        # 5. Buttons
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_cancel = QPushButton("Hủy bỏ")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("💾 Xác Nhận Thao Tác")
        btn_save.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold; padding: 8px 16px;")
        btn_save.clicked.connect(self._validate_and_save)

        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

        # Trigger cập nhật hiển thị field
        self._on_action_changed(0)

    def _on_action_changed(self, index):
        action_name = self.cbo_action.currentText().split()[0]
        
        # Ẩn hết trước
        self.txt_url.setEnabled(action_name == "navigate")
        self.cbo_loc_type.setEnabled(action_name in ["click", "fill", "wait_for", "read_text"])
        self.txt_loc_val.setEnabled(action_name in ["click", "fill", "wait_for", "read_text"])
        self.txt_fill_value.setEnabled(action_name == "fill")
        self.spin_wait_sec.setEnabled(action_name == "wait")

    def _load_existing_data(self, step: WorkflowStep):
        self.txt_id.setText(step.id)
        self.txt_desc.setText(step.description or "")
        
        # Set Action
        for i in range(self.cbo_action.count()):
            if self.cbo_action.itemText(i).startswith(step.action):
                self.cbo_action.setCurrentIndex(i)
                break

        # Set Risk
        for i in range(self.cbo_risk.count()):
            if self.cbo_risk.itemData(i) == step.risk_level.value:
                self.cbo_risk.setCurrentIndex(i)
                break

        params = step.params
        if "url" in params:
            self.txt_url.setText(str(params["url"]))
        if "value" in params:
            self.txt_fill_value.setText(str(params["value"]))
        if "seconds" in params:
            self.spin_wait_sec.setValue(int(params["seconds"]))

        if "locator" in params:
            loc = params["locator"]
            if isinstance(loc, dict):
                if "role" in loc:
                    self.cbo_loc_type.setCurrentText("role + name")
                    self.txt_loc_val.setText(loc.get("name", loc.get("role", "")))
                elif "label" in loc:
                    self.cbo_loc_type.setCurrentText("label")
                    self.txt_loc_val.setText(loc.get("label", ""))
                elif "placeholder" in loc:
                    self.cbo_loc_type.setCurrentText("placeholder")
                    self.txt_loc_val.setText(loc.get("placeholder", ""))
                elif "css" in loc:
                    self.cbo_loc_type.setCurrentText("css")
                    self.txt_loc_val.setText(loc.get("css", ""))
            elif isinstance(loc, str):
                self.cbo_loc_type.setCurrentText("css")
                self.txt_loc_val.setText(loc)

    def _validate_and_save(self):
        step_id = self.txt_id.text().strip()
        if not step_id:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập Mã bước (ID).")
            return
        
        action_name = self.cbo_action.currentText().split()[0]
        if action_name == "navigate" and not self.txt_url.text().strip():
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập URL cần mở.")
            return

        if action_name in ["click", "fill", "wait_for"] and not self.txt_loc_val.text().strip():
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập tiêu chí định vị phần tử (Locator).")
            return

        self.accept()

    def get_step(self) -> WorkflowStep:
        action_name = self.cbo_action.currentText().split()[0]
        risk = RiskLevel(self.cbo_risk.currentData())
        
        params = {}
        if action_name == "navigate":
            params["url"] = self.txt_url.text().strip()
            params["wait_until"] = "domcontentloaded"
        elif action_name == "wait":
            params["seconds"] = float(self.spin_wait_sec.value())
        elif action_name in ["click", "fill", "wait_for", "read_text"]:
            loc_type = self.cbo_loc_type.currentText()
            loc_val = self.txt_loc_val.text().strip()
            
            if loc_type == "role + name":
                params["locator"] = {"role": "button", "name": loc_val}
            elif loc_type == "label":
                params["locator"] = {"label": loc_val}
            elif loc_type == "placeholder":
                params["locator"] = {"placeholder": loc_val}
            elif loc_type == "text":
                params["locator"] = {"text": loc_val}
            elif loc_type == "css":
                params["locator"] = {"css": loc_val}

            if action_name == "fill":
                params["value"] = self.txt_fill_value.text().strip()

        return WorkflowStep(
            id=self.txt_id.text().strip(),
            action=action_name,
            description=self.txt_desc.text().strip() or None,
            risk_level=risk,
            params=params,
        )

