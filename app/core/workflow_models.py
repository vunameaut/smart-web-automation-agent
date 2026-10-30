"""Workflow Models - Định nghĩa cấu trúc Schema cho Workflow và Step."""

from enum import Enum
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Mức độ rủi ro của từng hành động theo tài liệu đặc tả (Mục 5)."""
    LOW = "low"            # Mở trang, đọc dữ liệu, chờ đợi
    MEDIUM = "medium"      # Thêm vào giỏ, điền form tạm thời
    HIGH = "high"          # Gửi đơn đăng ký, đặt hàng
    CRITICAL = "critical"  # Thanh toán, hành động không thể hoàn tác


class StepStatus(str, Enum):
    """Trạng thái thực thi của từng bước."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    WAITING_USER = "waiting_user"


class VerifyType(str, Enum):
    """Các loại điều kiện xác minh."""
    VISIBLE = "visible"
    HIDDEN = "hidden"
    TEXT_CONTAINS = "text_contains"
    URL_CONTAINS = "url_contains"
    VALUE_EQUALS = "value_equals"


class VerifyCondition(BaseModel):
    """Điều kiện kiểm tra trước hoặc xác minh sau hành động."""
    type: VerifyType
    locator: Optional[Union[Dict[str, Any], str]] = None
    value: Optional[str] = None
    timeout_ms: Optional[int] = Field(default=10000)


class WorkflowStep(BaseModel):
    """Định nghĩa một bước trong quy trình Workflow."""
    id: str = Field(..., description="ID duy nhất của step trong workflow")
    action: str = Field(..., description="Tên action: navigate, click, fill, wait_for, screenshot, assert, v.v.")
    description: Optional[str] = Field(default=None)
    risk_level: RiskLevel = Field(default=RiskLevel.LOW)
    timeout_ms: Optional[int] = Field(default=None)
    
    # Tham số động cho action
    params: Dict[str, Any] = Field(default_factory=dict)
    
    # Điều kiện trước khi thực hiện
    pre_condition: Optional[VerifyCondition] = Field(default=None)
    
    # Điều kiện xác minh sau khi thực hiện
    verify: Optional[VerifyCondition] = Field(default=None)


class StepExecutionResult(BaseModel):
    """Kết quả thực thi một bước."""
    step_id: str
    action: str
    status: StepStatus
    duration_ms: float = 0.0
    output: Optional[Any] = None
    error: Optional[str] = None
    screenshot_path: Optional[str] = None


class WorkflowDefinition(BaseModel):
    """Định nghĩa toàn bộ một quy trình Workflow."""
    name: str = Field(..., description="Tên workflow")
    version: int = Field(default=1)
    description: Optional[str] = Field(default=None)
    target_domains: List[str] = Field(default_factory=list, description="Danh sách domain được phép thao tác")
    steps: List[WorkflowStep] = Field(default_factory=list)

    @classmethod
    def from_yaml(cls, yaml_content: str) -> "WorkflowDefinition":
        import yaml
        data = yaml.safe_load(yaml_content)
        return cls(**data)

    def to_yaml(self) -> str:
        import yaml
        return yaml.dump(self.model_dump(), sort_keys=False, allow_unicode=True)

