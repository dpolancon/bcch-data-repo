"""
Purpose:  Enforce the repository's file-organisation rules -- the codes/ vs
          scripts/ language split, the stage-numbered script naming protocol,
          and the mandatory provenance header on every .py file.
Task:     Repository infrastructure
Inputs:   scripts/, codes/
Outputs:  n/a
Created:  2026-08-21
Updated:  2026-08-21
Owner:    dpolancon
"""

import ast
import re

import pytest

from lib.paths import CODES_DIR, REPO_ROOT, SCRIPTS_DIR

STAGE_NAME_RE = re.compile(r"^\d{2}_[a-z]+_[a-z0-9_]+\.py$")
ADHOC_NAME_RE = re.compile(r"^adhoc_\d{8}_[a-z0-9_]+\.py$")

REQUIRED_HEADER_FIELDS = ("Purpose:", "Task:", "Inputs:", "Outputs:", "Created:", "Updated:", "Owner:")
STAGE_ONLY_FIELDS = ("Stage:", "Run:")

LIB_DIR = SCRIPTS_DIR / "lib"


def stage_scripts():
    return sorted(p for p in SCRIPTS_DIR.glob("*.py") if p.name != "__init__.py")


def lib_modules():
    return sorted(p for p in LIB_DIR.glob("*.py") if p.name != "__init__.py")


def all_python_files():
    return stage_scripts() + lib_modules() + [LIB_DIR / "__init__.py"]


class TestLanguageSplit:
    """codes/ is R-only and scripts/ is Python-only -- the rule in CLAUDE.md."""

    def test_no_python_in_codes(self):
        offenders = [p.name for p in CODES_DIR.rglob("*.py")]
        assert not offenders, f"Python files in codes/ (R only): {offenders}"

    def test_no_r_in_scripts(self):
        offenders = [p.name for p in SCRIPTS_DIR.rglob("*.R")] + [
            p.name for p in SCRIPTS_DIR.rglob("*.r")
        ]
        assert not offenders, f"R files in scripts/ (Python only): {offenders}"

    def test_src_directory_is_gone(self):
        """src/ was dissolved into scripts/lib/; it must not reappear."""
        assert not (REPO_ROOT / "src").exists()


class TestNamingProtocol:
    @pytest.mark.parametrize("path", stage_scripts(), ids=lambda p: p.name)
    def test_runnable_scripts_are_stage_numbered(self, path):
        assert STAGE_NAME_RE.match(path.name) or ADHOC_NAME_RE.match(path.name), (
            f"{path.name} must match NN_verb_object.py (or adhoc_YYYYMMDD_purpose.py)"
        )

    def test_stage_numbers_are_unique(self):
        numbers = [p.name[:2] for p in stage_scripts() if STAGE_NAME_RE.match(p.name)]
        duplicates = {n for n in numbers if numbers.count(n) > 1}
        assert not duplicates, f"duplicate stage numbers: {duplicates}"

    @pytest.mark.parametrize("path", lib_modules(), ids=lambda p: p.name)
    def test_library_modules_are_not_stage_numbered(self, path):
        """Library names are an import surface and must stay stable."""
        assert not STAGE_NAME_RE.match(path.name)
        assert not path.name[:2].isdigit()


class TestProvenanceHeaders:
    @pytest.mark.parametrize("path", all_python_files(), ids=lambda p: p.name)
    def test_has_module_docstring(self, path):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        assert ast.get_docstring(tree), f"{path.name} has no module docstring"

    @pytest.mark.parametrize("path", all_python_files(), ids=lambda p: p.name)
    def test_header_carries_required_fields(self, path):
        doc = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8"))) or ""
        missing = [f for f in REQUIRED_HEADER_FIELDS if f not in doc]
        assert not missing, f"{path.name} header missing: {missing}"

    @pytest.mark.parametrize("path", stage_scripts(), ids=lambda p: p.name)
    def test_stage_scripts_declare_stage_and_run(self, path):
        doc = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8"))) or ""
        missing = [f for f in STAGE_ONLY_FIELDS if f not in doc]
        assert not missing, f"{path.name} header missing: {missing}"

    @pytest.mark.parametrize("path", all_python_files(), ids=lambda p: p.name)
    def test_dates_are_iso_formatted(self, path):
        doc = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8"))) or ""
        for field in ("Created:", "Updated:"):
            value = doc.split(field, 1)[1].splitlines()[0].strip()
            assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", value), (
                f"{path.name} {field} must be YYYY-MM-DD, got {value!r}"
            )


class TestCsvOnlyDataFormat:
    """Every data artifact is plain CSV -- see the rule in CLAUDE.md."""

    @pytest.mark.parametrize("path", all_python_files(), ids=lambda p: p.name)
    def test_no_parquet_io(self, path):
        text = path.read_text(encoding="utf-8")
        code_only = re.sub(r'""".*?"""', "", text, flags=re.DOTALL)
        offenders = re.findall(r"\b(?:to_parquet|read_parquet)\b", code_only)
        assert not offenders, f"{path.name} uses Parquet I/O: {set(offenders)}"

    def test_no_parquet_files_in_data(self):
        stray = [p.name for p in (REPO_ROOT / "data").rglob("*.parquet")]
        assert not stray, f"Parquet files under data/: {stray}"

    def test_pyarrow_is_not_a_dependency(self):
        pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        assert "pyarrow" not in pyproject


class TestDeclaredDependencies:
    """Every third-party import must appear in pyproject.toml.

    seaborn, matplotlib and numpy were all imported by reporting stages while
    undeclared, so a clean `pip install -e .` produced an environment that
    could not run them.
    """

    def test_no_undeclared_third_party_imports(self):
        import sys

        stdlib = set(sys.stdlib_module_names)
        local = {"lib"}
        found = set()
        for path in all_python_files():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    found.update(a.name.split(".")[0] for a in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                    found.add(node.module.split(".")[0])

        pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8").lower()
        # Distribution names may hyphenate where the module underscores.
        aliases = {"dotenv": "python-dotenv", "pydantic_settings": "pydantic-settings"}

        undeclared = [
            m
            for m in sorted(found - stdlib - local)
            if aliases.get(m, m).lower() not in pyproject
        ]
        assert not undeclared, f"imported but not declared in pyproject.toml: {undeclared}"


class TestNoDeadDuplicates:
    """The legacy stubs were strict subsets of the lib modules."""

    @pytest.mark.parametrize("name", ["api_client.py", "catalog_manager.py", "bcch_query_utility.py"])
    def test_legacy_stub_is_gone(self, name):
        assert not (SCRIPTS_DIR / name).exists()

    def test_no_lingering_src_imports(self):
        offenders = []
        for path in all_python_files() + list((REPO_ROOT / "tests").glob("*.py")):
            text = path.read_text(encoding="utf-8")
            if re.search(r"^\s*(from|import)\s+src\b", text, re.MULTILINE):
                offenders.append(path.name)
        assert not offenders, f"files still importing src.*: {offenders}"


class TestSecretsAreIgnored:
    """Credentials must be unreachable by git, and must stay that way."""

    @pytest.mark.parametrize(
        "relpath",
        ["secrets/.env", "secrets/token.txt", ".env", "secrets/anything.key"],
    )
    def test_credential_paths_are_gitignored(self, relpath):
        import subprocess

        result = subprocess.run(
            ["git", "check-ignore", "-q", relpath],
            cwd=REPO_ROOT, capture_output=True,
        )
        assert result.returncode == 0, f"{relpath} is NOT gitignored"

    @pytest.mark.parametrize("relpath", ["secrets/.env.example", "secrets/README.md"])
    def test_secrets_docs_stay_tracked(self, relpath):
        import subprocess

        result = subprocess.run(
            ["git", "check-ignore", "-q", relpath],
            cwd=REPO_ROOT, capture_output=True,
        )
        assert result.returncode != 0, f"{relpath} should be tracked, not ignored"

    def test_no_credential_file_is_tracked(self):
        import subprocess

        tracked = subprocess.run(
            ["git", "ls-files"], cwd=REPO_ROOT,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        ).stdout.split()
        bad = [
            f for f in tracked
            if f.endswith((".env", "token.txt", ".pem", ".key"))
            or ("credential" in f.lower())
        ]
        assert not bad, f"credential-looking files are tracked: {bad}"
