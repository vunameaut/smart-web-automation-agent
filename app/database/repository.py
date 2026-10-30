"""Repository - Tầng truy cập dữ liệu (Data Access Layer)."""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.database.database import get_db_session
from app.database.models import (
    WorkflowModel,
    TaskModel,
    ExecutionModel,
    StepExecutionModel,
    ArtifactModel,
    get_utc_now,
)
from app.core.workflow_models import WorkflowDefinition


class Repository:
    """Tập trung các thao tác đọc ghi Database SQLite."""

    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_db_session()

    # --- WORKFLOW CRUD ---
    def save_workflow(self, workflow_def: WorkflowDefinition, workflow_id: Optional[str] = None) -> WorkflowModel:
        raw_json = json.dumps(workflow_def.model_dump(), ensure_ascii=False)
        if workflow_id:
            wf = self.session.get(WorkflowModel, workflow_id)
            if wf:
                wf.name = workflow_def.name
                wf.version = workflow_def.version
                wf.definition_json = raw_json
                wf.updated_at = get_utc_now()
                self.session.commit()
                return wf

        wf = WorkflowModel(
            name=workflow_def.name,
            version=workflow_def.version,
            definition_json=raw_json,
        )
        self.session.add(wf)
        self.session.commit()
        self.session.refresh(wf)
        return wf

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowModel]:
        return self.session.get(WorkflowModel, workflow_id)

    def list_workflows(self) -> List[WorkflowModel]:
        stmt = select(WorkflowModel).order_by(desc(WorkflowModel.updated_at))
        return list(self.session.scalars(stmt).all())

    # --- TASK CRUD ---
    def create_task(
        self,
        name: str,
        workflow_id: str,
        description: Optional[str] = None,
        schedule_config: Optional[Dict[str, Any]] = None,
        priority: int = 1,
        approval_policy: str = "default",
        enabled: bool = True,
    ) -> TaskModel:
        task = TaskModel(
            name=name,
            workflow_id=workflow_id,
            description=description,
            schedule_config=json.dumps(schedule_config) if schedule_config else None,
            priority=priority,
            approval_policy=approval_policy,
            enabled=enabled,
        )
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def get_task(self, task_id: str) -> Optional[TaskModel]:
        return self.session.get(TaskModel, task_id)

    def list_tasks(self) -> List[TaskModel]:
        stmt = select(TaskModel).order_by(desc(TaskModel.priority), desc(TaskModel.updated_at))
        return list(self.session.scalars(stmt).all())

    # --- EXECUTION CRUD ---
    def create_execution(self, task_id: str, workflow_version: int = 1) -> ExecutionModel:
        exec_model = ExecutionModel(
            task_id=task_id,
            workflow_version=workflow_version,
            status="RUNNING",
            started_at=get_utc_now(),
        )
        self.session.add(exec_model)
        self.session.commit()
        self.session.refresh(exec_model)
        return exec_model

    def update_execution(
        self,
        execution_id: str,
        status: str,
        current_step_id: Optional[str] = None,
        last_error: Optional[str] = None,
        finished: bool = False,
    ) -> Optional[ExecutionModel]:
        exec_model = self.session.get(ExecutionModel, execution_id)
        if exec_model:
            exec_model.status = status
            if current_step_id is not None:
                exec_model.current_step_id = current_step_id
            if last_error is not None:
                exec_model.last_error = last_error
            if finished:
                exec_model.finished_at = get_utc_now()
            self.session.commit()
            return exec_model
        return None

    def record_step_execution(
        self,
        execution_id: str,
        step_id: str,
        status: str,
        attempt: int = 1,
        result_json: Optional[str] = None,
        error_category: Optional[str] = None,
    ) -> StepExecutionModel:
        step_exec = StepExecutionModel(
            execution_id=execution_id,
            step_id=step_id,
            status=status,
            attempt=attempt,
            started_at=get_utc_now(),
            finished_at=get_utc_now(),
            result_json=result_json,
            error_category=error_category,
        )
        self.session.add(step_exec)
        self.session.commit()
        return step_exec

    def record_artifact(
        self,
        execution_id: str,
        file_path: str,
        artifact_type: str = "screenshot",
        step_execution_id: Optional[str] = None,
    ) -> ArtifactModel:
        artifact = ArtifactModel(
            execution_id=execution_id,
            step_execution_id=step_execution_id,
            type=artifact_type,
            file_path=file_path,
            created_at=get_utc_now(),
        )
        self.session.add(artifact)
        self.session.commit()
        return artifact

