from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPOSITORY_ROOT / "initialize-codex-project" / "scripts"
CATALOG = (
    REPOSITORY_ROOT
    / "initialize-codex-project"
    / "references"
    / "engineering-standards"
    / "catalog.json"
)
sys.path.insert(0, str(SCRIPTS))

from select_language_profiles import load_catalog, select_profiles  # noqa: E402


class LanguageProfileSelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="language-profile-test-")
        self.root = Path(self.temporary.name)
        self.catalog = load_catalog(CATALOG)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write(self, relative: str, content: str = "test\n") -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def result(self, max_files: int = 200_000):
        return select_profiles(self.catalog, self.root, max_files=max_files)

    @staticmethod
    def ids(records):
        return [record["id"] for record in records]

    def test_selects_multiple_profiles_from_extensions(self) -> None:
        self.write("Sources/App.swift")
        self.write("tools/check.py")
        result = self.result()
        self.assertEqual(self.ids(result["selected_profiles"]), ["swift", "python"])
        self.assertFalse(result["execution_authorized"])
        self.assertFalse(result["truncated"])

    def test_selection_does_not_read_source_contents(self) -> None:
        self.write("src/main.py", "secret source content\n")
        with mock.patch("pathlib.Path.read_text", side_effect=AssertionError):
            result = select_profiles(self.catalog, self.root)
        self.assertEqual(self.ids(result["selected_profiles"]), ["python"])

    def test_selects_every_supported_language_profile(self) -> None:
        for relative in (
            "Sources/App.swift",
            "Sources/Legacy.mm",
            "app/src/main/App.kt",
            "server/src/Main.java",
            "web/src/index.ts",
            "web/index.html",
            "tools/check.py",
            "cmd/server/main.go",
            "crates/core/src/lib.rs",
            "native/legacy.c",
            "native/main.cpp",
        ):
            self.write(relative)
        result = self.result()
        self.assertEqual(
            self.ids(result["selected_profiles"]),
            [
                "swift",
                "objective-c",
                "kotlin",
                "java",
                "typescript-javascript",
                "web-frontend",
                "python",
                "go",
                "rust",
                "c",
                "cpp",
            ],
        )

    def test_objective_c_weak_extension_requires_project_marker(self) -> None:
        self.write("Sources/Legacy.m")
        ambiguous = self.result()
        self.assertNotIn("objective-c", self.ids(ambiguous["selected_profiles"]))
        self.assertIn("objective-c", self.ids(ambiguous["ambiguous_profiles"]))

        self.write("App.xcodeproj/project.pbxproj")
        selected = self.result()
        self.assertIn("objective-c", self.ids(selected["selected_profiles"]))
        self.assertNotIn("swift", self.ids(selected["selected_profiles"]))

    def test_header_without_marker_remains_ambiguous(self) -> None:
        self.write("include/value.h")
        self.write("CMakeLists.txt")
        result = self.result()
        self.assertEqual(
            self.ids(result["ambiguous_profiles"]), ["objective-c", "c", "cpp"]
        )

    def test_c_source_selects_c_without_cpp(self) -> None:
        self.write("src/value.c")
        result = self.result()
        self.assertEqual(self.ids(result["selected_profiles"]), ["c"])

    def test_frontend_source_augments_typescript_profile(self) -> None:
        self.write("src/App.tsx")
        self.write("public/index.html")
        result = self.result()
        self.assertEqual(
            self.ids(result["selected_profiles"]),
            ["typescript-javascript", "web-frontend"],
        )

    def test_tsx_without_web_evidence_keeps_frontend_ambiguous(self) -> None:
        self.write("src/App.tsx")
        result = self.result()
        self.assertEqual(
            self.ids(result["selected_profiles"]), ["typescript-javascript"]
        )
        self.assertIn("web-frontend", self.ids(result["ambiguous_profiles"]))

    def test_frontend_config_marker_selects_web_profile(self) -> None:
        self.write("angular.json", "{}\n")
        result = self.result()
        self.assertEqual(self.ids(result["selected_profiles"]), ["web-frontend"])

    def test_cpp_strong_extension_selects_profile(self) -> None:
        self.write("src/value.cpp")
        result = self.result()
        self.assertEqual(self.ids(result["selected_profiles"]), ["cpp"])

    def test_build_markers_select_language_profiles(self) -> None:
        self.write("go.mod", "module example.com/project\n")
        self.write("crates/example/Cargo.toml", "[package]\nname='example'\n")
        result = self.result()
        self.assertEqual(self.ids(result["selected_profiles"]), ["go", "rust"])

    def test_excluded_dependency_directory_is_ignored(self) -> None:
        self.write("node_modules/package/index.ts")
        result = self.result()
        self.assertNotIn("typescript-javascript", self.ids(result["selected_profiles"]))

    def test_swift_build_artifacts_do_not_change_language_evidence(self) -> None:
        self.write("ios/Package.swift")
        self.write("ios/Sources/App.swift")
        self.write("ios/App.xcodeproj/project.pbxproj")
        before = select_profiles(self.catalog, self.root, scopes=["ios"])
        self.write("ios/.build/out/Intermediates.noindex/GeneratedModuleMaps/App-Swift.h")
        self.write("ios/.build/out/DerivedSources/test_entry_point.swift")
        for scopes in ((), ("ios",)):
            with self.subTest(scopes=scopes):
                after = select_profiles(self.catalog, self.root, scopes=scopes, max_files=3)
                self.assertEqual(after["selected_profiles"], before["selected_profiles"])
                self.assertEqual(after["ambiguous_profiles"], [])
                self.assertEqual(after["scanned_files"], before["scanned_files"])
                self.assertFalse(after["truncated"])

    def test_explicit_swift_build_scope_remains_inspectable(self) -> None:
        self.write("ios/.build/DerivedSources/generated.c")
        for scope in ("ios/.build", "ios/.build/DerivedSources/generated.c"):
            with self.subTest(scope=scope):
                result = select_profiles(self.catalog, self.root, scopes=[scope])
                self.assertEqual(self.ids(result["selected_profiles"]), ["c"])
                self.assertEqual(result["scanned_files"], 1)

    def test_scan_budget_reports_truncation(self) -> None:
        self.write("a.py")
        self.write("b.py")
        result = self.result(max_files=1)
        self.assertTrue(result["truncated"])
        self.assertEqual(result["scanned_files"], 1)

    def test_catalog_has_expected_profile_ids(self) -> None:
        self.assertEqual(
            [profile["id"] for profile in self.catalog["profiles"]],
            [
                "swift",
                "objective-c",
                "kotlin",
                "java",
                "typescript-javascript",
                "web-frontend",
                "python",
                "go",
                "rust",
                "c",
                "cpp",
            ],
        )

    def test_scope_separates_application_from_tooling(self):
        self.write("app/main.go")
        self.write("tools/check.py")
        result = select_profiles(self.catalog, self.root, scopes=["app"], role="application")
        self.assertEqual(self.ids(result["selected_profiles"]), ["go"])
        self.assertEqual(result["scope"], {"paths": ["app"], "role": "application"})

    def test_overlapping_scopes_do_not_double_count(self):
        self.write("app/main.go")
        result = select_profiles(self.catalog, self.root, scopes=["app", "app/main.go"])
        self.assertEqual(result["scanned_files"], 1)

    def test_scope_cannot_escape_repository(self):
        from select_language_profiles import SelectionError
        with self.assertRaisesRegex(SelectionError, "unsafe scope"):
            select_profiles(self.catalog, self.root, scopes=["../outside"])


if __name__ == "__main__":
    unittest.main()
