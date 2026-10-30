"""Tests for UI components, StepEditorDialog and background worker."""

import pytest
import sys
from PySide6.QtWidgets import QApplication
from app.ui.step_dialog import StepEditorDialog
from app.core.workflow_models import WorkflowStep, RiskLevel


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def test_step_editor_dialog_creation(qapp):
    """Kiểm tra khởi tạo hộp thoại và lấy dữ liệu Step hợp lệ."""
    dialog = StepEditorDialog()
    dialog.txt_id.setText("test_step_click")
    dialog.txt_desc.setText("Nhấp chuột thử nghiệm")
    
    # Chọn action click
    dialog.cbo_action.setCurrentIndex(1)  # click
    dialog.txt_loc_val.setText("Xác nhận đăng ký")
    
    step = dialog.get_step()
    assert step.id == "test_step_click"
    assert step.action == "click"
    assert step.params["locator"] == {"role": "button", "name": "Xác nhận đăng ký"}


def test_step_editor_dialog_edit_mode(qapp):
    """Kiểm tra nạp dữ liệu bước có sẵn vào hộp thoại để chỉnh sửa."""
    existing_step = WorkflowStep(
        id="step_navigate_test",
        action="navigate",
        description="Mở trang web",
        risk_level=RiskLevel.LOW,
        params={"url": "https://example.com/test", "wait_until": "domcontentloaded"}
    )
    dialog = StepEditorDialog(step_data=existing_step)
    assert dialog.txt_id.text() == "step_navigate_test"
    assert dialog.txt_url.text() == "https://example.com/test"
    
    # Sửa URL
    dialog.txt_url.setText("https://updated.com")
    updated = dialog.get_step()
    assert updated.params["url"] == "https://updated.com"

