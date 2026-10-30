"""Task Manager - Quản lý CRUD nhiệm vụ, liên kết Workflow và lịch chạy."""

from typing import Optional, List, Dict, Any
from app.database.repository import Repository
from app.database.models import TaskModel, ExecutionModel
from app.core.scheduler import TaskScheduler
from app.utils.logging_config import get_logger

logger = get_logger("autoweb.task_manager")


class TaskManager:
    """Quản lý các tác vụ tự động hóa của người dùng."""

    def __init__(self, repository: Optional[Repository] = None, scheduler: Optional[TaskScheduler] = None):
        self.repo = repository or Repository()
        self.scheduler = scheduler or TaskScheduler(repository=self.repo)

    def create_task(
        self,
        name: str,
        workflow_id: str,
        description: Optional[str] = None,
        schedule_config: Optional[Dict[str, Any]] = None,
        variables: Optional[Dict[str, Any]] = None,
        priority: int = 1,
    ) -> TaskModel:
        """Tạo một task mới có lưu trữ cấu hình biến."""
        task = self.repo.create_task(
            name=name,
            workflow_id=workflow_id,
            description=description,
            schedule_config=schedule_config,
            variables=variables,
            priority=priority,
        )
        logger.info(f"Đã tạo Task mới: [{task.id}] - '{task.name}'")
        return task

    def list_tasks(self) -> List[TaskModel]:
        """Lấy danh sách tất cả các task theo thứ tự ưu tiên."""
        return self.repo.list_tasks()

    def get_task(self, task_id: str) -> Optional[TaskModel]:
        """Lấy chi tiết một task."""
        return self.repo.get_task(task_id)

    def toggle_task(self, task_id: str, enabled: Optional[bool] = None) -> Optional[TaskModel]:
        """Bật hoặc tắt task."""
        task = self.repo.get_task(task_id)
        if task:
            task.enabled = not task.enabled if enabled is None else enabled
            self.repo.session.commit()
            logger.info(f"Task [{task_id}] trạng thái enabled đổi thành: {task.enabled}")
            return task
        return None

    def update_variables(self, task_id: str, variables: Dict[str, Any]) -> Optional[TaskModel]:
        """Cập nhật biến dữ liệu cho task."""
        return self.repo.update_task_variables(task_id, variables)

    def update_schedule(self, task_id: str, schedule_config: Optional[Dict[str, Any]]) -> Optional[TaskModel]:
        """Cập nhật cấu hình lịch cho task."""
        return self.repo.update_task_schedule(task_id, schedule_config)

    async def run_now(
        self,
        task_id: str,
        dry_run: bool = False,
        custom_variables: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Kích hoạt chạy ngay một task mà không chờ lịch."""
        logger.info(f"Kích hoạt chạy ngay Task [{task_id}] (dry_run={dry_run})...")
        return await self.scheduler.execute_task_run(
            task_id=task_id,
            dry_run=dry_run,
            custom_variables=custom_variables,
        )
