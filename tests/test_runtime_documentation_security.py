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

_CREDENTIALED_URL = re.compile(
    r"(?i)\b[a-z][a-z0-9+.-]*://[^\s/@:]+:[^\s/@]+@",
)
_LITERAL_PASSWORD_BULLET = re.compile(
    r"(?im)^\* Password："
    r"(?!`(?:环境变量|文件引用|<|\$\{))",
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

        self.assertEqual([], findings)

    def test_implementation_plan_requires_external_secret_and_rotation(
        self,
    ) -> None:
        text = IMPLEMENTATION_PLAN.read_text(encoding="utf-8")

        self.assertIn("NS_RUNTIME_REDIS_PASSWORD", text)
        self.assertIn("${NS_RUNTIME_REDIS_URL}", text)
        self.assertIn("必须由人工在 Redis 侧轮换/吊销", text)
        self.assertNotRegex(text, _CREDENTIALED_URL)
        self.assertNotRegex(text, _LITERAL_PASSWORD_BULLET)


if __name__ == "__main__":
    unittest.main()
