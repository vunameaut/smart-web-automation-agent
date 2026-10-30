"""Tests for Database Persistence, Task Manager, Scheduler & Recovery Engine - Phase 3 & 4."""

import pytest
from pathlib import Path
from datetime import datetime, timezone, timedelta
from app.database.database import init_db
from app.database.repository import Repository
from app.database.models import Base
from app.core.task_manager import TaskManager
from app.core.scheduler import TaskScheduler
from app.core.recovery_engine import RecoveryEngine, ErrorCategory, RetryPolicy
from app.core.workflow_models import WorkflowDefinition, WorkflowStep


@pytest.fixture
def test_repo(tmp_path: Path) -> Repository:
    """Khởi tạo SQLite database tạm thời phục vụ unit test."""
    test_db = tmp_path / "test_autoweb.db"
    session_factory = init_db(test_db)
    return Repository(session_factory())


def test_database_crud(test_repo: Repository):
    """Kiểm tra lưu và đọc Workflow, Task, Execution trong SQLite."""
    # 1. Lưu Workflow
    wf_def = WorkflowDefinition(
        name="Test DB Workflow",
        steps=[WorkflowStep(id="s1", action="wait", params={"seconds": 0.1})],
    )
    wf_model = test_repo.save_workflow(wf_def)
    assert wf_model.id is not None
    assert wf_model.name == "Test DB Workflow"

    # 2. Tạo Task
    task = test_repo.create_task(
        name="Test Task 1",
        workflow_id=wf_model.id,
        priority=5,
    )
    assert task.id is not None
    assert task.priority == 5
    assert task.enabled is True

    # 3. Tạo Execution
    execution = test_repo.create_execution(task_id=task.id)
    assert execution.status == "RUNNING"

    # 4. Cập nhật Execution
    updated = test_repo.update_execution(execution.id, status="SUCCEEDED", finished=True)
    assert updated.status == "SUCCEEDED"
    assert updated.finished_at is not None


def test_task_manager_toggle(test_repo: Repository):
    """Kiểm tra bật tắt trạng thái task qua TaskManager."""
    wf_def = WorkflowDefinition(name="WF Toggle", steps=[])
    wf = test_repo.save_workflow(wf_def)

    tm = TaskManager(repository=test_repo)
    task = tm.create_task(name="Task To Toggle", workflow_id=wf.id)
    assert task.enabled is True

    tm.toggle_task(task.id)
    toggled = tm.get_task(task.id)
    assert toggled.enabled is False


def test_recovery_engine_classification():
    """Kiểm tra phân loại lỗi và phát hiện CAPTCHA / 500 / Timeout."""
    # 1. Phát hiện CAPTCHA qua DOM
    captcha_cat = RecoveryEngine.classify_error(
        Exception("Timeout"),
        page_content="<html><body>Vui lòng giải mã CAPTCHA để tiếp tục</body></html>"
    )
    assert captcha_cat == ErrorCategory.CAPTCHA_OR_MFA
    assert not RecoveryEngine.is_retryable(captcha_cat)

    # 2. Phát hiện HTTP 503
    server_cat = RecoveryEngine.classify_error(Exception("Server returned HTTP 503 Service Unavailable"))
    assert server_cat == ErrorCategory.SERVER_ERROR_5XX
    assert RecoveryEngine.is_retryable(server_cat)

    # 3. Tính toán Backoff Delay
    policy = RetryPolicy(base_delay_seconds=1.0, backoff_factor=2.0, enable_jitter=False)
    assert policy.calculate_delay(0) == 1.0
    assert policy.calculate_delay(1) == 2.0
    assert policy.calculate_delay(2) == 4.0


@pytest.mark.asyncio
async def test_scheduler_immediate_task_run(test_repo: Repository):
    """Kiểm tra kích hoạt chạy ngay một task qua TaskScheduler."""
    wf_def = WorkflowDefinition(
        name="WF Immediate Run",
        steps=[WorkflowStep(id="step_w", action="wait", params={"seconds": 0.2})],
    )
    wf_model = test_repo.save_workflow(wf_def)
    task = test_repo.create_task(name="Task Immediate", workflow_id=wf_model.id)

    scheduler = TaskScheduler(repository=test_repo)
    result = await scheduler.execute_task_run(task.id)

    assert result["status"] == "SUCCEEDED"
    assert "execution_id" in result

