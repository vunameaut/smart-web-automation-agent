"""Workflow Engine - Thực thi quy trình tự động hóa có kiểm soát."""

import time
from typing import Optional, Dict, Any, List
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.browser.browser_controller import BrowserController
from app.browser.locator_helper import resolve_locator
from app.core.workflow_models import (
    WorkflowDefinition,
    WorkflowStep,
    StepExecutionResult,
    StepStatus,
    VerifyCondition,
    VerifyType,
    RiskLevel,
)
from app.core.action_registry import ActionRegistry, get_action_registry
from app.core.recovery_engine import RecoveryEngine, RetryPolicy, ErrorCategory
from app.actions.base import ActionContext
from app.utils.logging_config import get_logger

logger = get_logger("autoweb.engine")


class VerificationError(Exception):
    """Lỗi khi điều kiện xác minh trước hoặc sau hành động không đạt."""
    pass


class WorkflowEngine:
    """Động cơ điều phối và thực thi Workflow tuần tự có kiểm chứng & Recovery."""

    def __init__(
        self,
        registry: Optional[ActionRegistry] = None,
        recovery_engine: Optional[RecoveryEngine] = None,
    ):
        self.registry = registry or get_action_registry()
        self.recovery = recovery_engine or RecoveryEngine()

    async def verify_condition(
        self,
        condition: VerifyCondition,
        context: ActionContext,
    ) -> bool:
        """Kiểm tra điều kiện (pre_condition hoặc post_verify)."""
        page = context.browser.page
        timeout = condition.timeout_ms or 10000

        try:
            if condition.type == VerifyType.URL_CONTAINS:
                expected = context.resolve_template(condition.value or "")
                current_url = page.url
                if expected not in current_url:
                    raise VerificationError(
                        f"URL hiện tại '{current_url}' không chứa giá trị mong đợi '{expected}'"
                    )
                return True

            elif condition.type == VerifyType.VISIBLE:
                if not condition.locator:
                    raise VerificationError("VerifyType.VISIBLE yêu cầu 'locator'.")
                loc = resolve_locator(page, condition.locator)
                await loc.wait_for(state="visible", timeout=timeout)
                return True

            elif condition.type == VerifyType.HIDDEN:
                if not condition.locator:
                    raise VerificationError("VerifyType.HIDDEN yêu cầu 'locator'.")
                loc = resolve_locator(page, condition.locator)
                await loc.wait_for(state="hidden", timeout=timeout)
                return True

            elif condition.type == VerifyType.TEXT_CONTAINS:
                if not condition.locator:
                    raise VerificationError("VerifyType.TEXT_CONTAINS yêu cầu 'locator'.")
                expected = context.resolve_template(condition.value or "")
                loc = resolve_locator(page, condition.locator)
                await loc.wait_for(state="visible", timeout=timeout)
                text = await loc.inner_text(timeout=timeout)
                if expected not in text:
                    raise VerificationError(
                        f"Văn bản thực tế '{text.strip()}' không chứa '{expected}'"
                    )
                return True

            elif condition.type == VerifyType.VALUE_EQUALS:
                if not condition.locator:
                    raise VerificationError("VerifyType.VALUE_EQUALS yêu cầu 'locator'.")
                expected = context.resolve_template(condition.value or "")
                loc = resolve_locator(page, condition.locator)
                await loc.wait_for(state="visible", timeout=timeout)
                val = await loc.input_value(timeout=timeout)
                if val != expected:
                    raise VerificationError(f"Giá trị ô nhập '{val}' không bằng '{expected}'")
                return True

            else:
                raise VerificationError(f"Loại kiểm tra không hỗ trợ: {condition.type}")

        except Exception as e:
            if isinstance(e, VerificationError):
                raise
            raise VerificationError(f"Xác minh điều kiện thất bại: {e}")

    async def execute_step(
        self,
        step: WorkflowStep,
        context: ActionContext,
    ) -> StepExecutionResult:
        """Thực thi một bước đơn lẻ với tích hợp Recovery Engine, retry và backoff."""
        start_time = time.perf_counter()
        action_name = step.action.lower()
        action_impl = self.registry.get(action_name)

        if not action_impl:
            return StepExecutionResult(
                step_id=step.id,
                action=step.action,
                status=StepStatus.FAILED,
                error=f"Không tìm thấy Action '{step.action}' trong ActionRegistry.",
            )

        logger.info(f"==> Bắt đầu thực thi Step [{step.id}] (Action: {step.action}, Risk: {step.risk_level.value})")

        # 1. Kiểm tra Pre-condition nếu có
        if step.pre_condition:
            logger.info(f"[{step.id}] Đang kiểm tra điều kiện tiên quyết (Pre-condition)...")
            try:
                await self.verify_condition(step.pre_condition, context)
                logger.info(f"[{step.id}] Pre-condition đạt yêu cầu.")
            except Exception as e:
                err_msg = f"Pre-condition không đạt: {e}"
                logger.error(f"[{step.id}] {err_msg}")
                shot = await context.browser.take_screenshot(f"err_pre_{step.id}")
                return StepExecutionResult(
                    step_id=step.id,
                    action=step.action,
                    status=StepStatus.FAILED,
                    error=err_msg,
                    screenshot_path=str(shot) if shot else None,
                    duration_ms=(time.perf_counter() - start_time) * 1000,
                )

        # 2. Xử lý chế độ Dry Run với các hành động High/Critical
        if context.dry_run and step.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            logger.warning(
                f"[DRY-RUN] Dừng trước bước có rủi ro cao [{step.id}] (Action: {step.action}, Risk: {step.risk_level.value})."
            )
            return StepExecutionResult(
                step_id=step.id,
                action=step.action,
                status=StepStatus.SKIPPED,
                output="Skipped: Stopped before high-risk impact step in dry-run mode",
                duration_ms=(time.perf_counter() - start_time) * 1000,
            )

        # 3. Thực thi Action chính kết nối Recovery Engine (Retry Policy)
        output = None
        policy = RetryPolicy(max_retries=2, base_delay_seconds=1.0)
        
        async def _do_action():
            return await action_impl.execute(context, step.params)

        def _get_dom():
            try:
                return context.browser.page.content()
            except Exception:
                return ""

        try:
            # Thực thi có phục hồi
            output = await self.recovery.execute_with_recovery(
                action_fn=_do_action,
                policy=policy,
                get_dom_fn=_get_dom,
            )
        except Exception as e:
            err_msg = f"Thực thi Action '{step.action}' thất bại sau recovery: {e}"
            logger.error(f"[{step.id}] {err_msg}")
            shot = await context.browser.take_screenshot(f"err_exec_{step.id}")
            return StepExecutionResult(
                step_id=step.id,
                action=step.action,
                status=StepStatus.FAILED,
                error=err_msg,
                screenshot_path=str(shot) if shot else None,
                duration_ms=(time.perf_counter() - start_time) * 1000,
            )

        # 4. Kiểm tra điều kiện xác minh sau hành động (Post-verify)
        if step.verify:
            logger.info(f"[{step.id}] Đang kiểm tra xác minh sau hành động (Post-verify)...")
            try:
                await self.verify_condition(step.verify, context)
                logger.info(f"[{step.id}] Post-verify thành công.")
            except Exception as e:
                err_msg = f"Post-verify thất bại: {e}"
                logger.error(f"[{step.id}] {err_msg}")
                shot = await context.browser.take_screenshot(f"err_verify_{step.id}")
                return StepExecutionResult(
                    step_id=step.id,
                    action=step.action,
                    status=StepStatus.FAILED,
                    error=err_msg,
                    screenshot_path=str(shot) if shot else None,
                    duration_ms=(time.perf_counter() - start_time) * 1000,
                )

        duration = (time.perf_counter() - start_time) * 1000
        logger.info(f"<== Hoàn thành Step [{step.id}] trong {duration:.1f}ms - Trạng thái: SUCCESS")
        return StepExecutionResult(
            step_id=step.id,
            action=step.action,
            status=StepStatus.SUCCESS,
            output=output,
            duration_ms=duration,
        )

    async def run_workflow(
        self,
        workflow: WorkflowDefinition,
        browser: BrowserController,
        dry_run: bool = False,
        initial_variables: Optional[Dict[str, Any]] = None,
    ) -> List[StepExecutionResult]:
        """Thực thi toàn bộ quy trình Workflow."""
        context = ActionContext(
            browser=browser,
            variables=initial_variables or {},
            dry_run=dry_run,
            target_domains=workflow.target_domains,
        )

        logger.info(
            f"=== BẮT ĐẦU WORKFLOW '{workflow.name}' (v{workflow.version}, Steps: {len(workflow.steps)}, Dry-run: {dry_run}) ==="
        )

        results: List[StepExecutionResult] = []

        for step in workflow.steps:
            res = await self.execute_step(step, context)
            results.append(res)
            if res.status == StepStatus.FAILED:
                logger.error(f"Workflow dừng lại do bước [{step.id}] thất bại: {res.error}")
                break
            if context.dry_run and res.status == StepStatus.SKIPPED:
                logger.info(f"[DRY-RUN] Dừng workflow tại bước [{step.id}] trước khi có tác động nghiệp vụ.")
                break

        succeeded = all(r.status in [StepStatus.SUCCESS, StepStatus.SKIPPED] for r in results)
        logger.info(
            f"=== KẾT THÚC WORKFLOW '{workflow.name}' - Kết quả: {'THÀNH CÔNG' if succeeded else 'THẤT BẠI'} ==="
        )
        return results
