"""Database Models - Định nghĩa các bảng SQLite bằng SQLAlchemy theo tài liệu đặc tả."""

import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    String,
    Integer,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class WorkflowModel(Base):
    __tablename__ = "workflows"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    definition_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

    tasks: Mapped[List["TaskModel"]] = relationship("TaskModel", back_populates="workflow")


class TaskModel(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    workflow_id: Mapped[str] = mapped_column(String(36), ForeignKey("workflows.id"), nullable=False)
    schedule_config: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON cron/datetime
    variables_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)   # JSON chứa biến cho task
    storage_state_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # File lưu session/cookies
    priority: Mapped[int] = mapped_column(Integer, default=1)
    approval_policy: Mapped[str] = mapped_column(String(50), default="default")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

    workflow: Mapped["WorkflowModel"] = relationship("WorkflowModel", back_populates="tasks")
    executions: Mapped[List["ExecutionModel"]] = relationship("ExecutionModel", back_populates="task")

    __table_args__ = (
        Index("idx_tasks_enabled_priority", "enabled", "priority"),
    )


class ExecutionModel(Base):
    __tablename__ = "executions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id: Mapped[str] = mapped_column(String(36), ForeignKey("tasks.id"), nullable=False)
    workflow_version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(50), default="READY")  # READY, RUNNING, SUCCEEDED, FAILED...
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    current_step_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    browser_profile_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    task: Mapped["TaskModel"] = relationship("TaskModel", back_populates="executions")
    step_executions: Mapped[List["StepExecutionModel"]] = relationship("StepExecutionModel", back_populates="execution")
    artifacts: Mapped[List["ArtifactModel"]] = relationship("ArtifactModel", back_populates="execution")

    __table_args__ = (
        Index("idx_executions_task_status", "task_id", "status"),
        Index("idx_executions_started_at", "started_at"),
    )


class StepExecutionModel(Base):
    __tablename__ = "step_executions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    execution_id: Mapped[str] = mapped_column(String(36), ForeignKey("executions.id"), nullable=False)
    step_id: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING")
    attempt: Mapped[int] = mapped_column(Integer, default=1)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    result_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    execution: Mapped["ExecutionModel"] = relationship("ExecutionModel", back_populates="step_executions")


class ArtifactModel(Base):
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    execution_id: Mapped[str] = mapped_column(String(36), ForeignKey("executions.id"), nullable=False)
    step_execution_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    type: Mapped[str] = mapped_column(String(50), default="screenshot")
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)

    execution: Mapped["ExecutionModel"] = relationship("ExecutionModel", back_populates="artifacts")


class AppSettingModel(Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value_json: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)
