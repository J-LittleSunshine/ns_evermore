# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT_DIR = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT_DIR / "docs"
IMPLEMENTATION_PLAN = (
    DOCS_DIR / "ns_runtime_implementation_plan_for_design_0.0.2.md"
)
RUNTIME_WORKFLOW = ROOT_DIR / ".github" / "workflows" / "ns-runtime.yml"

_CREDENTIALED_URL = re.compile(
    r"(?i)\b[a-z][a-z0-9+.-]*://[^\s/@:]+:[^\s/@]+@",
)
_LITERAL_PASSWORD_BULLET = re.compile(
    r"(?im)^\* Password："
    r"(?!`(?:环境变量|文件引用|<|\$\{))",
)
_PASSWORD_STORAGE_PERMISSION = re.compile(
    r"密码可以保存在\s+implementation plan",
)


class RuntimeDocumentationSecurityTestCase(unittest.TestCase):

    def test_runtime_documents_do_not_embed_userinfo_credentials(self) -> None:
        findings: list[str] = []
        for path in sorted(DOCS_DIR.glob("ns_runtime_*.md")):
            text = path.read_text(encoding="utf-8")
            if _CREDENTIALED_URL.search(text):
                findings.append(f"{path.name}:credentialed_url")
            if _LITERAL_PASSWORD_BULLET.search(text):
                findings.append(f"{path.name}:literal_password")
            if _PASSWORD_STORAGE_PERMISSION.search(text):
                findings.append(f"{path.name}:password_storage_permission")

        self.assertEqual([], findings)

    def test_implementation_plan_requires_external_secret_and_rotation(
        self,
    ) -> None:
        text = IMPLEMENTATION_PLAN.read_text(encoding="utf-8")

        self.assertIn("NS_RUNTIME_REDIS_PASSWORD", text)
        self.assertIn("${NS_RUNTIME_REDIS_URL}", text)
        self.assertIn("必须由人工在 Redis 侧轮换/吊销", text)
        self.assertIn(
            "仓库值已移除，服务端轮换待人工确认",
            text,
        )
        self.assertIn(
            "在该文件进入默认分支 `main` 前，GitHub Actions "
            "人工触发入口不可用",
            text,
        )
        self.assertIn(
            "当前修复候选在本记录时没有对应远端 run，保持 `UNVERIFIED`",
            text,
        )
        self.assertNotRegex(text, _CREDENTIALED_URL)
        self.assertNotRegex(text, _LITERAL_PASSWORD_BULLET)
        self.assertNotRegex(text, _PASSWORD_STORAGE_PERMISSION)

    def test_runtime_ci_has_manual_real_redis_and_commit_range_gates(
        self,
    ) -> None:
        text = RUNTIME_WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("workflow_dispatch:", text)
        self.assertIn("fetch-depth: 0", text)
        self.assertIn("apt-get install --yes redis-server", text)
        self.assertIn(
            'NS_RUNTIME_REQUIRE_REDIS_INTEGRATION: "1"',
            text,
        )
        self.assertIn("tests.test_redis_state_store_integration", text)
        self.assertIn(
            'git diff --check "${base_sha}" "${GITHUB_SHA}"',
            text,
        )
        self.assertIn(
            'git show --check --format= "${GITHUB_SHA}"',
            text,
        )
        self.assertNotRegex(text, _CREDENTIALED_URL)

    def test_p12_and_external_redis_rotation_status_remain_frozen(self) -> None:
        text = IMPLEMENTATION_PLAN.read_text(encoding="utf-8")

        self.assertIn(
            "| P12 | ACK/NACK/Defer/Timeout/Retry | `NOT_STARTED` | F0 | P11 |",
            text,
        )
        self.assertIn(
            "| 当前工作包状态 | `BLOCKED`（awaiting explicit authorization） |",
            text,
        )
        self.assertIn(
            "仓库值已移除，服务端轮换待人工确认",
            text,
        )


if __name__ == "__main__":
    unittest.main()
