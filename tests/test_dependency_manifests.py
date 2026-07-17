# -*- coding: utf-8 -*-
from __future__ import annotations

import re
import unittest
from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]

MANIFEST_NAMES = (
    "requirements-common.txt",
    "requirements-backend.txt",
    "requirements-runtime.txt",
    "requirements-runtime-test.txt",
    "requirements-runtime-benchmark.txt",
)

EXPECTED_INCLUDES = {
    "requirements-common.txt": (),
    "requirements-backend.txt": ("requirements-common.txt",),
    "requirements-runtime.txt": ("requirements-common.txt",),
    "requirements-runtime-test.txt": ("requirements-runtime.txt",),
    "requirements-runtime-benchmark.txt": ("requirements-runtime-test.txt",),
}

EXPECTED_DIRECT_PACKAGES = {
    "requirements-common.txt": frozenset(
        {
            "anyio",
            "certifi",
            "concurrent-log-handler",
            "exceptiongroup",
            "h11",
            "httpcore",
            "httpx",
            "idna",
            "portalocker",
            "typing-extensions",
        }
    ),
    "requirements-backend.txt": frozenset(
        {
            "adrf",
            "asgiref",
            "async-property",
            "cffi",
            "cryptography",
            "django",
            "djangorestframework",
            "joserfc",
            "pycparser",
            "sqlparse",
        }
    ),
    "requirements-runtime.txt": frozenset({"uvloop", "websockets"}),
    "requirements-runtime-test.txt": frozenset({"redis", "valkey"}),
    "requirements-runtime-benchmark.txt": frozenset({"pyperf", "psutil"}),
}

QUIC_EXPERIMENT_PACKAGES = frozenset(
    {
        "aioquic",
        "pylsqpack",
        "qh3",
    }
)

_REQUIREMENT_PATTERN = re.compile(
    r"^(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)"
    r"==(?P<version>[^;\s]+)"
    r"(?:\s*;\s*(?P<marker>.+))?$"
)


def _normalize_package_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).casefold()


@dataclass(frozen=True, slots=True)
class ParsedRequirement:
    name: str
    version: str
    marker: str | None


@dataclass(frozen=True, slots=True)
class ParsedManifest:
    includes: tuple[str, ...]
    requirements: tuple[ParsedRequirement, ...]


def _parse_manifest(name: str) -> ParsedManifest:
    path = ROOT_DIR / name
    includes: list[str] = []
    requirements: list[ParsedRequirement] = []

    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("-r "):
            include_name = line[3:].strip()
            include_path = Path(include_name)
            if include_path.is_absolute() or include_path.name != include_name:
                raise AssertionError(
                    f"{name}:{line_number}: include must be a root-level filename"
                )
            includes.append(include_name)
            continue

        match = _REQUIREMENT_PATTERN.fullmatch(line)
        if match is None:
            raise AssertionError(
                f"{name}:{line_number}: requirement must use an exact == pin"
            )

        requirements.append(
            ParsedRequirement(
                name=_normalize_package_name(match.group("name")),
                version=match.group("version"),
                marker=match.group("marker"),
            )
        )

    return ParsedManifest(
        includes=tuple(includes),
        requirements=tuple(requirements),
    )


def _resolved_package_names(
    name: str,
    manifests: dict[str, ParsedManifest],
    visiting: frozenset[str] = frozenset(),
) -> frozenset[str]:
    if name in visiting:
        raise AssertionError(f"cyclic requirements include detected at {name}")

    manifest = manifests[name]
    packages = {requirement.name for requirement in manifest.requirements}
    for include in manifest.includes:
        if include not in manifests:
            raise AssertionError(f"{name} includes unknown manifest {include}")
        packages.update(
            _resolved_package_names(
                include,
                manifests,
                visiting | {name},
            )
        )
    return frozenset(packages)


class RequirementManifestTests(unittest.TestCase):
    def _load_manifests(self) -> dict[str, ParsedManifest]:
        return {name: _parse_manifest(name) for name in MANIFEST_NAMES}

    def test_all_dependency_layers_exist(self) -> None:
        missing = [name for name in MANIFEST_NAMES if not (ROOT_DIR / name).is_file()]
        self.assertEqual(missing, [])

    def test_include_graph_is_explicit_and_acyclic(self) -> None:
        manifests = self._load_manifests()
        actual_includes = {
            name: manifest.includes for name, manifest in manifests.items()
        }
        self.assertEqual(actual_includes, EXPECTED_INCLUDES)

        for name in MANIFEST_NAMES:
            _resolved_package_names(name, manifests)

    def test_each_direct_dependency_is_exactly_pinned_once(self) -> None:
        manifests = self._load_manifests()
        for name, manifest in manifests.items():
            package_names = [requirement.name for requirement in manifest.requirements]
            with self.subTest(manifest=name):
                self.assertEqual(len(package_names), len(set(package_names)))
                self.assertEqual(
                    frozenset(package_names),
                    EXPECTED_DIRECT_PACKAGES[name],
                )
                self.assertTrue(
                    all(requirement.version for requirement in manifest.requirements)
                )

    def test_uvloop_is_platform_guarded_and_other_pins_are_unconditional(self) -> None:
        manifests = self._load_manifests()
        marked = {
            requirement.name: requirement.marker
            for manifest in manifests.values()
            for requirement in manifest.requirements
            if requirement.marker is not None
        }
        self.assertEqual(
            marked,
            {"uvloop": 'platform_system != "Windows"'},
        )

    def test_production_manifests_do_not_pull_test_or_benchmark_tools(self) -> None:
        manifests = self._load_manifests()
        runtime_packages = _resolved_package_names(
            "requirements-runtime.txt",
            manifests,
        )
        backend_packages = _resolved_package_names(
            "requirements-backend.txt",
            manifests,
        )
        test_only = EXPECTED_DIRECT_PACKAGES["requirements-runtime-test.txt"]
        benchmark_only = EXPECTED_DIRECT_PACKAGES[
            "requirements-runtime-benchmark.txt"
        ]
        runtime_only = EXPECTED_DIRECT_PACKAGES["requirements-runtime.txt"]

        self.assertTrue(runtime_packages.isdisjoint(test_only | benchmark_only))
        self.assertTrue(
            backend_packages.isdisjoint(
                runtime_only | test_only | benchmark_only | QUIC_EXPERIMENT_PACKAGES
            )
        )

    def test_runtime_layers_are_strict_supersets(self) -> None:
        manifests = self._load_manifests()
        production = _resolved_package_names(
            "requirements-runtime.txt",
            manifests,
        )
        test = _resolved_package_names(
            "requirements-runtime-test.txt",
            manifests,
        )
        benchmark = _resolved_package_names(
            "requirements-runtime-benchmark.txt",
            manifests,
        )

        self.assertLess(production, test)
        self.assertLess(test, benchmark)
        self.assertEqual(test - production, {"redis", "valkey"})
        self.assertEqual(benchmark - test, {"pyperf", "psutil"})

    def test_quic_experiments_are_deferred_from_every_manifest(self) -> None:
        manifests = self._load_manifests()
        all_packages = frozenset().union(
            *(
                _resolved_package_names(name, manifests)
                for name in MANIFEST_NAMES
            )
        )
        self.assertTrue(all_packages.isdisjoint(QUIC_EXPERIMENT_PACKAGES))


if __name__ == "__main__":
    unittest.main()
