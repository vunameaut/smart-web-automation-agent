"""Scheduler & Pre-warming Service - Lên lịch và chuẩn bị phiên tự động hóa."""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Callable
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.database.repository import Repository
from app.database.models import TaskModel, get_utc_now
from app.core.workflow_models import WorkflowDefinition
from app.core.workflow_engine import WorkflowEngine
from app.browser.browser_controller import BrowserController
from app.utils.logging_config import get_logger

logger = get_logger("autoweb.scheduler")


class TaskScheduler:
    """Điều phối lịch chạy và khởi động sớm trình duyệt (Pre-warming)."""

    def __init__(self, repository: Optional[Repository] = None):
        self.repo = repository or Repository()
        self.scheduler = AsyncIOScheduler(timezone="UTC")
        self.engine = WorkflowEngine()
        self._running_prewarmed_browsers: Dict[str, BrowserController] = {}

    def start(self) -> None:
        """Khởi động bộ lập lịch APScheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("TaskScheduler đã được kích hoạt thành công.")

    def shutdown(self) -> None:
        """Dừng bộ lập lịch."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("TaskScheduler đã dừng.")

    async def pre_warm_browser(self, task_id: str, target_url: Optional[str] = None) -> BrowserController:
        """Pre-warming: Khởi động trước browser và điều hướng sẵn tới trang."""
        logger.info(f"[PRE-WARMING] Đang khởi động sẵn Browser cho Task [{task_id}]...")
        browser = BrowserController(headless=False)
        await browser.start()
        if target_url:
            logger.info(f"[PRE-WARMING] Điều hướng sớm tới: {target_url}")
            await browser.navigate(target_url)
        self._running_prewarmed_browsers[task_id] = browser
        logger.info(f"[PRE-WARMING] Đã sẵn sàng trình duyệt cho Task [{task_id}].")
        return browser

    async def execute_task_run(
        self,
        task_id: str,
        dry_run: bool = False,
        planned_trigger_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Thực thi một lần chạy nhiệm vụ (task run)."""
        actual_trigger_time = get_utc_now()
        task = self.repo.get_task(task_id)
        if not task:
            logger.error(f"Không tìm thấy Task [{task_id}] trong Database.")
            return {"status": "FAILED", "error": "Task not found"}

        if not task.enabled:
            logger.warning(f"Task [{task_id}] '{task.name}' đang bị vô hiệu hóa (disabled). Bỏ qua.")
            return {"status": "SKIPPED", "error": "Task disabled"}

        # Đọc workflow definition từ database
        wf_model = self.repo.get_workflow(task.workflow_id)
        if not wf_model:
            logger.error(f"Không tìm thấy Workflow [{task.workflow_id}] gắn với Task.")
            return {"status": "FAILED", "error": "Workflow not found"}

        import json
        wf_data = json.loads(wf_model.definition_json)
        workflow_def = WorkflowDefinition(**wf_data)

        # Tạo bản ghi Execution trong Database
        execution = self.repo.create_execution(task_id=task.id, workflow_version=wf_model.version)
        logger.info(
            f"Bắt đầu thực thi Task [{task.name}] (Exec ID: {execution.id}) | Dự kiến: {planned_trigger_time} | Thực tế: {actual_trigger_time}"
        )

        # Sử dụng browser đã pre-warmed nếu có, hoặc tạo mới
        browser = self._running_prewarmed_browsers.pop(task_id, None)
        owns_browser = False
        if not browser or not browser.is_running:
            browser = BrowserController(headless=False)
            await browser.start()
            owns_browser = True

        # Cung cấp biến mặc định nếu template biến chưa có
        from pathlib import Path
        test_fixture_url = (self.repo.session.bind.url.database and Path(__file__).parent.parent.parent / "tests" / "fixtures" / "test_page.html").as_uri()
        default_vars = {
            "portal_url": test_fixture_url,
            "student_name": "Nguyễn Văn A",
            "course_code": "CS101-AUTOMATION",
        }

        try:
            results = await self.engine.run_workflow(
                workflow=workflow_def,
                browser=browser,
                dry_run=dry_run,
                initial_variables=default_vars,
            )

            # Cập nhật kết quả từng step vào database
            for res in results:
                self.repo.record_step_execution(
                    execution_id=execution.id,
                    step_id=res.step_id,
                    status=res.status.value,
                    result_json=str(res.output) if res.output else None,
                    error_category=res.error,
                )
                if res.screenshot_path:
                    self.repo.record_artifact(
                        execution_id=execution.id,
                        file_path=res.screenshot_path,
                        artifact_type="screenshot",
                    )

            overall_status = "SUCCEEDED" if all(r.status.value in ["success", "skipped"] for r in results) else "FAILED"
            self.repo.update_execution(
                execution_id=execution.id,
                status=overall_status,
                finished=True,
            )
            return {"status": overall_status, "execution_id": execution.id, "results": results}

        except Exception as e:
            logger.error(f"Lỗi khi thực thi Task [{task.name}]: {e}")
            self.repo.update_execution(
                execution_id=execution.id,
                status="FAILED",
                last_error=str(e),
                finished=True,
            )
            return {"status": "FAILED", "error": str(e)}

        finally:
            if owns_browser and browser:
                await browser.stop()

    def schedule_once(
        self,
        task_id: str,
        run_at: datetime,
        pre_warm_seconds: int = 0,
        pre_warm_url: Optional[str] = None,
    ) -> str:
        """Lên lịch chạy một lần tại thời điểm UTC xác định."""
        job_id = f"task_{task_id}_once"

        # Nếu có pre-warming, lên lịch mở browser sớm hơn
        if pre_warm_seconds > 0:
            pre_warm_time = run_at - timedelta(seconds=pre_warm_seconds)
            if pre_warm_time > get_utc_now():
                prewarm_job_id = f"task_{task_id}_prewarm"
                self.scheduler.add_job(
                    self.pre_warm_browser,
                    trigger=DateTrigger(run_date=pre_warm_time, timezone=timezone.utc),
                    args=[task_id, pre_warm_url],
                    id=prewarm_job_id,
                    replace_existing=True,
                )
                logger.info(f"Đã lên lịch Pre-warming cho Task [{task_id}] vào lúc {pre_warm_time} UTC.")

        self.scheduler.add_job(
            self.execute_task_run,
            trigger=DateTrigger(run_date=run_at, timezone=timezone.utc),
            args=[task_id, False, run_at],
            id=job_id,
            replace_existing=True,
        )
        logger.info(f"Đã lên lịch kích hoạt Task [{task_id}] vào lúc {run_at} UTC.")
        return job_id

