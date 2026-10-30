"""Kiểm thử tính năng Workflow Recorder và Parser."""

import pytest
from app.core.workflow_recorder import WorkflowRecorder
from app.core.workflow_models import RiskLevel


SAMPLE_CODEGEN_SCRIPT = '''
from playwright.sync_api import Playwright, sync_api, expect

def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    page.goto("https://portal.example.com/login")
    page.get_by_label("Tên đăng nhập:").fill("sinhvien_01")
    page.get_by_placeholder("Nhập mật khẩu").fill("matkhau_bi_mat")
    page.get_by_role("button", name="Đăng nhập hệ thống").click()
    page.get_by_text("Xem lịch học").click()
    page.locator("#course-item-123").click()
    page.get_by_role("button", name="Xác nhận đăng ký học phần").click()
    page.wait_for_timeout(2000)

    context.close()
    browser.close()
'''


def test_workflow_recorder_parsing():
    wf = WorkflowRecorder.parse_script(SAMPLE_CODEGEN_SCRIPT, workflow_name="Test Recorded Workflow")
    
    assert wf.name == "Test Recorded Workflow"
    assert len(wf.steps) == 9  # 8 recorded steps + 1 final screenshot
    
    # Step 1: Navigate
    assert wf.steps[0].action == "navigate"
    assert wf.steps[0].params["url"] == "https://portal.example.com/login"
    assert wf.steps[0].risk_level == RiskLevel.LOW

    # Step 2: Fill username
    assert wf.steps[1].action == "fill"
    assert wf.steps[1].params["locator"] == {"label": "Tên đăng nhập:"}
    assert wf.steps[1].params["value"] == "sinhvien_01"

    # Step 3: Fill password
    assert wf.steps[2].action == "fill"
    assert wf.steps[2].params["locator"] == {"placeholder": "Nhập mật khẩu"}
    assert wf.steps[2].params["value"] == "matkhau_bi_mat"

    # Step 4: Click login button
    assert wf.steps[3].action == "click"
    assert wf.steps[3].params["locator"] == {"role": "button", "name": "Đăng nhập hệ thống"}
    assert wf.steps[3].risk_level == RiskLevel.MEDIUM

    # Step 5: Click text
    assert wf.steps[4].action == "click"
    assert wf.steps[4].params["locator"] == {"text": "Xem lịch học"}

    # Step 6: Click CSS locator
    assert wf.steps[5].action == "click"
    assert wf.steps[5].params["locator"] == {"css": "#course-item-123"}

    # Step 7: High risk click ("Xác nhận đăng ký")
    assert wf.steps[6].action == "click"
    assert wf.steps[6].risk_level == RiskLevel.HIGH

    # Step 8: Wait
    assert wf.steps[7].action == "wait"
    assert wf.steps[7].params["seconds"] == 2.0

    # Step 9: Final screenshot
    assert wf.steps[8].action == "screenshot"


def test_workflow_recorder_to_yaml():
    wf = WorkflowRecorder.parse_script(SAMPLE_CODEGEN_SCRIPT, workflow_name="YAML Export Test")
    yaml_text = wf.to_yaml()
    assert "name: YAML Export Test" in yaml_text
    assert "action: navigate" in yaml_text
    assert "action: fill" in yaml_text
