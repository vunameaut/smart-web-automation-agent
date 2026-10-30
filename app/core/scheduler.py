"""Scheduler & Pre-warming Service - Lên lịch và chuẩn bị phiên tự động hóa."""

import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Callable
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import get_settings
from app.database.repository import Repository
from app.database.database import get_db_session
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
        self.settings = get_settings()
        self.scheduler = AsyncIOScheduler(timezone="UTC")
        self.engine = WorkflowEngine()
        self._running_prewarmed_browsers: Dict[str, BrowserController] = {}

    def start(self) -> None:
        """Khởi động bộ lập lịch APScheduler và nạp lại lịch đã lưu."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("TaskScheduler đã được kích hoạt thành công.")
            self.load_persisted_schedules()

    def shutdown(self) -> None:
        """Dừng bộ lập lịch."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("TaskScheduler đã dừng.")

    def load_persisted_schedules(self) -> None:
        """Đọc schedule_config từ DB và nạp vào APScheduler khi khởi động app."""
        tasks = self.repo.list_tasks()
        logger.info(f"Đang kiểm tra và nạp lịch trình cho {len(tasks)} nhiệm vụ...")
        for task in tasks:
            if not task.enabled or not task.schedule_config:
                continue
            try:
                cfg = json.loads(task.schedule_config)
                # 1. Chạy 1 lần theo ISO timestamp: {"run_at": "2026-10-30T15:00:00Z"}
                if "run_at" in cfg:
                    run_at = datetime.fromisoformat(cfg["run_at"].replace("Z", "+00:00"))
                    if run_at > get_utc_now():
                        self.schedule_once(
                            task_id=task.id,
                            run_at=run_at,
                            pre_warm_seconds=cfg.get("pre_warm_seconds", 0),
                        )
                # 2. Chạy lặp lại theo chu kỳ phút: {"interval_minutes": 30}
                elif "interval_minutes" in cfg:
                    minutes = int(cfg["interval_minutes"])
                    job_id = f"task_{task.id}_interval"
                    self.scheduler.add_job(
                        self.execute_task_run,
                        trigger=IntervalTrigger(minutes=minutes, timezone=timezone.utc),
                        args=[task.id, False],
                        id=job_id,
                        replace_existing=True,
                    )
                    logger.info(f"Đã nạp lịch định kỳ mỗi {minutes} phút cho Task [{task.id}] '{task.name}'.")
            except Exception as e:
                logger.error(f"Không thể nạp lịch cho Task [{task.id}]: {e}")

    async def pre_warm_browser(self, task_id: str, target_url: Optional[str] = None) -> BrowserController:
        """Pre-warming: Khởi động trước browser theo cấu hình headless và điều hướng sẵn."""
        logger.info(f"[PRE-WARMING] Đang khởi động sẵn Browser cho Task [{task_id}]...")
        browser = BrowserController(
            headless=self.settings.HEADLESS,
            slow_mo_ms=self.settings.SLOW_MO_MS,
            timeout_ms=self.settings.DEFAULT_TIMEOUT_MS,
        )
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
        custom_variables: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Thực thi một lần chạy nhiệm vụ (task run) với toàn bộ quản lý try/finally an toàn."""
        actual_trigger_time = get_utc_now()
        
        # Mỗi lần chạy tạo một session DB độc lập
        session = get_db_session()
        local_repo = Repository(session=session)

        task = local_repo.get_task(task_id)
        if not task:
            logger.error(f"Không tìm thấy Task [{task_id}] trong Database.")
            session.close()
            return {"status": "FAILED", "error": "Task not found"}

        if not task.enabled:
            logger.warning(f"Task [{task_id}] '{task.name}' đang bị vô hiệu hóa (disabled). Bỏ qua.")
            session.close()
            return {"status": "SKIPPED", "error": "Task disabled"}

        wf_model = local_repo.get_workflow(task.workflow_id)
        if not wf_model:
            logger.error(f"Không tìm thấy Workflow [{task.workflow_id}] gắn với Task.")
            session.close()
            return {"status": "FAILED", "error": "Workflow not found"}

        wf_data = json.loads(wf_model.definition_json)
        workflow_def = WorkflowDefinition(**wf_data)

        # Lấy biến được lưu trong Task hoặc custom_variables
        variables = {}
        if task.variables_json:
            try:
                variables.update(json.loads(task.variables_json))
            except Exception:
                pass
        
        # Nếu task chưa có biến, nạp fallback mặc định cho workflow mẫu
        if not variables:
            from pathlib import Path
            test_fixture_url = (Path(__file__).parent.parent.parent / "tests" / "fixtures" / "test_page.html").as_uri()
            variables = {
                "portal_url": test_fixture_url,
                "student_name": "Nguyễn Văn A",
                "course_code": "CS101-AUTOMATION",
            }

        if custom_variables:
            variables.update(custom_variables)

        # Tạo bản ghi Execution trong Database
        execution = local_repo.create_execution(task_id=task.id, workflow_version=wf_model.version)
        logger.info(
            f"Bắt đầu thực thi Task [{task.name}] (Exec ID: {execution.id}) | Headless: {self.settings.HEADLESS} | Dry-run: {dry_run}"
        )

        # Sử dụng browser đã pre-warmed hoặc khởi tạo mới (đọc HEADLESS từ settings)
        browser = self._running_prewarmed_browsers.pop(task_id, None)
        owns_browser = False
        if not browser or not browser.is_running:
            storage_path = task.storage_state_path or str(self.settings.PROFILES_DIR / f"profile_{task.id}.json")
            browser = BrowserController(
                headless=self.settings.HEADLESS,
                slow_mo_ms=self.settings.SLOW_MO_MS,
                timeout_ms=self.settings.DEFAULT_TIMEOUT_MS,
                storage_state_path=storage_path,
            )
            await browser.start()
            owns_browser = True

        try:
            results = await self.engine.run_workflow(
                workflow=workflow_def,
                browser=browser,
                dry_run=dry_run,
                initial_variables=variables,
            )

            for res in results:
                local_repo.record_step_execution(
                    execution_id=execution.id,
                    step_id=res.step_id,
                    status=res.status.value,
                    result_json=str(res.output) if res.output else None,
                    error_category=res.error,
                )
                if res.screenshot_path:
                    local_repo.record_artifact(
                        execution_id=execution.id,
                        file_path=res.screenshot_path,
                        artifact_type="screenshot",
                    )

            overall_status = "SUCCEEDED" if all(r.status.value in ["success", "skipped"] for r in results) else "FAILED"
            local_repo.update_execution(
                execution_id=execution.id,
                status=overall_status,
                finished=True,
            )
            return {"status": overall_status, "execution_id": execution.id, "results": results}

        except Exception as e:
            logger.error(f"Lỗi khi thực thi Task [{task.name}]: {e}")
            local_repo.update_execution(
                execution_id=execution.id,
                status="FAILED",
                last_error=str(e),
                finished=True,
            )
            return {"status": "FAILED", "error": str(e)}

        finally:
            if owns_browser and browser:
                try:
                    await browser.stop()
                except Exception as e:
                    logger.warning(f"Lỗi khi đóng browser: {e}")
            session.close()

    def schedule_once(
        self,
        task_id: str,
        run_at: datetime,
        pre_warm_seconds: int = 0,
        pre_warm_url: Optional[str] = None,
    ) -> str:
        """Lên lịch chạy một lần tại thời điểm UTC xác định."""
        job_id = f"task_{task_id}_once"

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
