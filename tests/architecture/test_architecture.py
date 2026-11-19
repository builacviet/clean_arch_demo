import ast
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SRC_DIR = ROOT_DIR / "src"
DOMAIN_DIR = SRC_DIR / "domain"
APPLICATION_DIR = SRC_DIR / "application"
UNIT_TEST_DIR = ROOT_DIR / "tests" / "unit"


def _iter_python_files(directory: Path) -> list[Path]:
    return [p for p in directory.rglob("*.py") if p.name != "__init__.py"]


class TestCleanArchitectureRules(unittest.TestCase):
    def test_no_forbidden_builtins_or_dynamic_imports_in_core(self) -> None:
        forbidden_funcs = {"print", "open", "eval", "exec", "__import__"}

        for target_dir in (DOMAIN_DIR, APPLICATION_DIR):
            for file_path in _iter_python_files(target_dir):
                tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            self.assertNotEqual(
                                alias.name,
                                "importlib",
                                f"VIOLATION in {file_path}:{node.lineno} - "
                                "Dynamic import 'importlib' is forbidden.",
                            )
                    elif isinstance(node, ast.ImportFrom) and node.module == "importlib":
                        self.fail(
                            f"VIOLATION in {file_path}:{node.lineno} - "
                            "Dynamic import from 'importlib' is forbidden."
                        )
                    elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                        self.assertNotIn(
                            node.func.id,
                            forbidden_funcs,
                            f"VIOLATION in {file_path}:{node.lineno} - "
                            f"Built-in '{node.func.id}()' is forbidden in core layers.",
                        )

    def test_use_case_dependencies_must_be_typed_and_not_any(self) -> None:
        for file_path in _iter_python_files(APPLICATION_DIR):
            if "use_cases" not in file_path.parts:
                continue

            tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name.endswith("UseCase"):
                    init_methods = [
                        n
                        for n in node.body
                        if isinstance(n, ast.FunctionDef) and n.name == "__init__"
                    ]
                    self.assertTrue(
                        init_methods,
                        f"VIOLATION in {file_path}:{node.lineno} - "
                        f"{node.name} must define '__init__' for Dependency Injection.",
                    )
                    for arg in init_methods[0].args.args:
                        if arg.arg == "self":
                            continue
                        self.assertIsNotNone(
                            arg.annotation,
                            f"VIOLATION in {file_path}:{arg.lineno} - "
                            f"Parameter '{arg.arg}' in {node.name}.__init__ lacks a type hint.",
                        )
                        if isinstance(arg.annotation, ast.Name):
                            self.assertNotEqual(
                                arg.annotation.id,
                                "Any",
                                f"VIOLATION in {file_path}:{arg.lineno} - "
                                f"Parameter '{arg.arg}' in {node.name}.__init__ cannot use 'Any'.",
                            )

    def test_every_use_case_must_have_corresponding_unit_test(self) -> None:
        unit_test_files = list(UNIT_TEST_DIR.rglob("test_*.py"))
        unit_test_names = {f.stem for f in unit_test_files}

        for file_path in _iter_python_files(APPLICATION_DIR):
            if "use_cases" not in file_path.parts:
                continue

            expected_prefix = f"test_{file_path.stem}"
            matching_tests = [f for f in unit_test_files if f.stem.startswith(expected_prefix)]
            self.assertTrue(
                matching_tests,
                f"VIOLATION in {file_path} - Missing mandatory unit test file "
                f"'tests/unit/{expected_prefix}*.py' (found: {sorted(unit_test_names)}).",
            )

            has_test_func = False
            for test_file in matching_tests:
                test_tree = ast.parse(
                    test_file.read_text(encoding="utf-8"), filename=str(test_file)
                )
                for node in ast.walk(test_tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
                        node.name.startswith("test_")
                    ):
                        has_test_func = True
                        break
            self.assertTrue(
                has_test_func,
                f"VIOLATION in {matching_tests} - "
                "Unit test file must contain at least one 'test_*' method.",
            )

    def test_ports_must_follow_interface_naming_convention(self) -> None:
        for file_path in _iter_python_files(APPLICATION_DIR):
            if not file_path.name.startswith("ports"):
                continue

            tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    is_valid = (
                        node.name.startswith("I") and len(node.name) > 1 and node.name[1].isupper()
                    )
                    self.assertTrue(
                        is_valid,
                        f"VIOLATION in {file_path}:{node.lineno} - "
                        f"Port class '{node.name}' must start with 'I' (e.g., I{node.name}).",
                    )

    def test_domain_entities_must_not_inherit_external_base_classes(self) -> None:
        forbidden_bases = {"BaseModel", "Base", "DeclarativeBase"}

        for file_path in _iter_python_files(DOMAIN_DIR):
            if not file_path.name.startswith("entities"):
                continue

            tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            self.assertNotIn(
                                base.id,
                                forbidden_bases,
                                f"VIOLATION in {file_path}:{node.lineno} - "
                                f"Domain entity '{node.name}' cannot inherit from '{base.id}'.",
                            )


if __name__ == "__main__":
    unittest.main()
