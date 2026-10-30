"""Workflow Recorder & Parser - Tự động ghi lại thao tác người dùng thành Workflow có cấu trúc.

Sử dụng Playwright Codegen để mở trình duyệt tương tác, người dùng chỉ cần thao tác bằng chuột
và bàn phím. Hệ thống phân tích mã nguồn sinh ra bằng AST để trích xuất thành danh sách WorkflowStep.
"""

import ast
import re
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from app.core.workflow_models import WorkflowDefinition, WorkflowStep, RiskLevel
from app.utils.logging_config import get_logger

logger = get_logger("autoweb.recorder")

# Các từ khóa hành động nhạy cảm cần gán RiskLevel.HIGH
HIGH_RISK_KEYWORDS = [
    "thanh toán", "pay", "checkout", "mua", "buy", "order", "đặt hàng",
    "submit", "gửi", "xóa", "delete", "remove", "đăng ký", "register",
    "confirm", "xác nhận", "transfer", "chuyển tiền"
]


def _evaluate_ast_node(node: ast.AST) -> Any:
    """Đánh giá an toàn giá trị của AST literal node."""
    try:
        return ast.literal_eval(node)
    except Exception:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return node.value
        return ast.unparse(node)


def _extract_locator_from_call(target_call: ast.Call) -> Tuple[Dict[str, Any], str]:
    """Trích xuất cấu hình Locator và chuỗi mô tả từ một ast.Call của Playwright."""
    if not isinstance(target_call.func, ast.Attribute):
        return {"css": ast.unparse(target_call)}, ast.unparse(target_call)

    func_name = target_call.func.attr
    locator: Dict[str, Any] = {}
    label_desc = ""

    # 1. page.get_by_role("button", name="Đăng nhập")
    if func_name == "get_by_role":
        role = _evaluate_ast_node(target_call.args[0]) if target_call.args else "button"
        name = None
        for kw in target_call.keywords:
            if kw.arg == "name":
                name = _evaluate_ast_node(kw.value)
        locator["role"] = str(role)
        if name:
            locator["name"] = str(name)
            label_desc = f"{role} '{name}'"
        else:
            label_desc = f"{role}"

    # 2. page.get_by_label("Tên đăng nhập:")
    elif func_name == "get_by_label":
        lbl = _evaluate_ast_node(target_call.args[0]) if target_call.args else ""
        locator["label"] = str(lbl)
        label_desc = f"nhãn '{lbl}'"

    # 3. page.get_by_placeholder("Nhập mật khẩu")
    elif func_name == "get_by_placeholder":
        ph = _evaluate_ast_node(target_call.args[0]) if target_call.args else ""
        locator["placeholder"] = str(ph)
        label_desc = f"ô gợi ý '{ph}'"

    # 4. page.get_by_text("Đăng ký ngay")
    elif func_name == "get_by_text":
        txt = _evaluate_ast_node(target_call.args[0]) if target_call.args else ""
        locator["text"] = str(txt)
        label_desc = f"chữ '{txt}'"

    # 5. page.locator("...")
    elif func_name == "locator":
        css_or_sel = _evaluate_ast_node(target_call.args[0]) if target_call.args else ""
        locator["css"] = str(css_or_sel)
        label_desc = f"phần tử '{css_or_sel}'"

    else:
        raw = ast.unparse(target_call)
        locator["css"] = raw
        label_desc = raw

    return locator, label_desc


def _determine_risk_level(action: str, label_desc: str) -> RiskLevel:
    """Tự động phân loại mức độ rủi ro dựa trên thao tác và tên phần tử."""
    if action == "navigate":
        return RiskLevel.LOW

    desc_lower = label_desc.lower()
    for kw in HIGH_RISK_KEYWORDS:
        if kw in desc_lower:
            return RiskLevel.HIGH

    if action in ["fill", "click"]:
        return RiskLevel.MEDIUM

    return RiskLevel.LOW


class WorkflowRecorder:
    """Bộ ghi nhận và chuyển đổi mã sinh từ Playwright sang WorkflowDefinition."""

    @staticmethod
    def parse_script(script_content: str, workflow_name: str = "Kịch bản tự động ghi nhận") -> WorkflowDefinition:
        """Phân tích nội dung mã Python sinh bởi Playwright Codegen thành WorkflowDefinition."""
        steps: List[WorkflowStep] = []
        step_idx = 1

        try:
            tree = ast.parse(script_content)
        except Exception as e:
            logger.error(f"Lỗi cú pháp khi phân tích mã Playwright: {e}")
            raise ValueError(f"Không thể phân tích mã kịch bản: {e}")

        # Duyệt tất cả các biểu thức gọi hàm trong AST
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)):
                continue

            call = node.value
            if not isinstance(call.func, ast.Attribute):
                continue

            method_name = call.func.attr
            target_obj = call.func.value

            # 1. Điều hướng: page.goto("URL")
            if method_name == "goto" and isinstance(target_obj, ast.Name):
                url = _evaluate_ast_node(call.args[0]) if call.args else ""
                steps.append(
                    WorkflowStep(
                        id=f"step_{step_idx}_navigate",
                        action="navigate",
                        description=f"Mở trang web {url}",
                        risk_level=RiskLevel.LOW,
                        params={"url": str(url), "wait_until": "domcontentloaded"},
                    )
                )
                step_idx += 1

            # 2. Nhấp chuột: target.click()
            elif method_name in ["click", "check"] and isinstance(target_obj, ast.Call):
                loc, desc = _extract_locator_from_call(target_obj)
                risk = _determine_risk_level("click", desc)
                steps.append(
                    WorkflowStep(
                        id=f"step_{step_idx}_click",
                        action="click",
                        description=f"Nhấp chuột vào {desc}",
                        risk_level=risk,
                        params={"locator": loc},
                    )
                )
                step_idx += 1

            # 3. Nhập liệu: target.fill("value")
            elif method_name == "fill" and isinstance(target_obj, ast.Call):
                val = _evaluate_ast_node(call.args[0]) if call.args else ""
                loc, desc = _extract_locator_from_call(target_obj)
                steps.append(
                    WorkflowStep(
                        id=f"step_{step_idx}_fill",
                        action="fill",
                        description=f"Nhập liệu '{val}' vào {desc}",
                        risk_level=RiskLevel.MEDIUM,
                        params={"locator": loc, "value": str(val)},
                    )
                )
                step_idx += 1

            # 4. Chờ thời gian: page.wait_for_timeout(ms)
            elif method_name == "wait_for_timeout":
                ms = _evaluate_ast_node(call.args[0]) if call.args else 1000
                sec = max(1.0, round(float(ms) / 1000.0, 1))
                steps.append(
                    WorkflowStep(
                        id=f"step_{step_idx}_wait",
                        action="wait",
                        description=f"Dừng chờ trong {sec} giây",
                        risk_level=RiskLevel.LOW,
                        params={"seconds": sec},
                    )
                )
                step_idx += 1

        # Nếu có các bước, thêm một bước chụp ảnh màn hình lưu bằng chứng ở cuối
        if steps:
            steps.append(
                WorkflowStep(
                    id=f"step_{step_idx}_screenshot",
                    action="screenshot",
                    description="Chụp ảnh màn hình lưu bằng chứng hoàn thành",
                    risk_level=RiskLevel.LOW,
                    params={"filename": "recorded_final_shot.png"},
                )
            )

        logger.info(f"Đã trích xuất thành công {len(steps)} bước hành động từ mã ghi nhận.")
        return WorkflowDefinition(
            name=workflow_name,
            version=1,
            description="Kịch bản được ghi nhận tự động từ thao tác người dùng.",
            steps=steps,
        )
