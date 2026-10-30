"""Tests for Workflow Engine and Action Registry - Phase 2."""

import pytest
from pathlib import Path
from app.browser import BrowserController
from app.core import (
    WorkflowEngine,
    WorkflowDefinition,
    WorkflowStep,
    StepStatus,
    RiskLevel,
    VerifyCondition,
    VerifyType,
)


@pytest.fixture
def test_page_url() -> str:
    html_path = Path(__file__).parent / "fixtures" / "test_page.html"
    return html_path.as_uri()


def test_workflow_yaml_parsing():
    """Kiểm tra đọc và parse file YAML thành WorkflowDefinition."""
    yaml_file = Path(__file__).parent.parent / "workflows" / "course_registration.yaml"
    content = yaml_file.read_text(encoding="utf-8")
    wf = WorkflowDefinition.from_yaml(content)
    
    assert wf.name == "Đăng ký học phần thử nghiệm"
    assert len(wf.steps) == 7
    assert wf.steps[0].id == "step_open_portal"
    assert wf.steps[4].risk_level == RiskLevel.HIGH


@pytest.mark.asyncio
async def test_workflow_execution_success(test_page_url: str):
    """Kiểm tra thực thi workflow tuần tự thành công toàn bộ các bước."""
    yaml_file = Path(__file__).parent.parent / "workflows" / "course_registration.yaml"
    content = yaml_file.read_text(encoding="utf-8")
    wf = WorkflowDefinition.from_yaml(content)

    engine = WorkflowEngine()
    async with BrowserController(headless=True) as browser:
        results = await engine.run_workflow(
            workflow=wf,
            browser=browser,
            initial_variables={
                "portal_url": test_page_url,
                "student_name": "Trần Thị B",
                "course_code": "CS202-ALGORITHMS",
            },
        )

        assert len(results) == 7
        assert all(r.status == StepStatus.SUCCESS for r in results)
        
        # Kiểm tra bước read_text đã đọc đúng kết quả
        read_step = results[5]
        assert read_step.action == "read_text"
        assert "Trần Thị B" in read_step.output


@pytest.mark.asyncio
async def test_workflow_dry_run_protection(test_page_url: str):
    """Chế độ Dry Run phải bỏ qua các bước có risk_level HIGH hoặc CRITICAL."""
    yaml_file = Path(__file__).parent.parent / "workflows" / "course_registration.yaml"
    content = yaml_file.read_text(encoding="utf-8")
    wf = WorkflowDefinition.from_yaml(content)

    engine = WorkflowEngine()
    async with BrowserController(headless=True) as browser:
        results = await engine.run_workflow(
            workflow=wf,
            browser=browser,
            dry_run=True,
            initial_variables={
                "portal_url": test_page_url,
                "student_name": "Lê Văn C",
                "course_code": "CS303-SECURITY",
            },
        )

        # Bước thứ 5 là submit (risk_level: high) -> phải bị SKIPPED
        submit_step = results[4]
        assert submit_step.action == "click"
        assert submit_step.status == StepStatus.SKIPPED


@pytest.mark.asyncio
async def test_workflow_verification_failure_stops_execution(test_page_url: str):
    """Nếu một bước xác minh thất bại, workflow phải dừng lại ngay lập tức."""
    wf = WorkflowDefinition(
        name="Test Verify Failure",
        steps=[
            WorkflowStep(
                id="step_1",
                action="navigate",
                params={"url": test_page_url},
                verify=VerifyCondition(
                    type=VerifyType.TEXT_CONTAINS,
                    locator={"css": "h2"},
                    value="TIÊU ĐỀ KHÔNG TỒN TẠI",
                    timeout_ms=500,
                )
            ),
            WorkflowStep(
                id="step_2",
                action="wait",
                params={"seconds": 1.0},
            )
        ]
    )

    engine = WorkflowEngine()
    async with BrowserController(headless=True) as browser:
        results = await engine.run_workflow(wf, browser)
        assert len(results) == 1  # Chỉ chạy đến step 1 rồi dừng
        assert results[0].status == StepStatus.FAILED
        assert "không chứa" in results[0].error

