"""Tests for Domain Security validation."""

import pytest
from app.actions.base import ActionContext, DomainSecurityViolation
from app.browser import BrowserController


def test_target_domains_security_allow():
    """Kiểm tra domain hợp lệ được cho phép."""
    ctx = ActionContext(
        browser=None,
        target_domains=["example.com", "edu.vn"],
    )
    # Hợp lệ
    ctx.validate_domain("https://example.com/login")
    ctx.validate_domain("https://sub.example.com/dashboard")
    ctx.validate_domain("https://portal.edu.vn")
    ctx.validate_domain("file:///D:/test.html")


def test_target_domains_security_block():
    """Kiểm tra chặn domain lạ không nằm trong whitelist."""
    ctx = ActionContext(
        browser=None,
        target_domains=["example.com"],
    )
    with pytest.raises(DomainSecurityViolation):
        ctx.validate_domain("https://malicious-site.com/hack")

