"""Language, framework, monorepo detection from project manifests.

Replaces detect-language.sh with a pure-Python implementation.
Reads manifest files (package.json, pyproject.toml, go.mod, etc.) to determine
the language stack, framework, test framework, and package manager for a project.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class DetectionResult:
    language: str = "unknown"
    framework: str = "unknown"
    test_framework: str = "unknown"
    package_manager: str = "unknown"


@dataclass
class WorkspaceInfo:
    name: str
    root: str
    detection: DetectionResult


@dataclass
class ProjectInfo:
    type: str  # 'single' or 'monorepo'
    workspaces: list[WorkspaceInfo]
    detection: DetectionResult  # Root-level detection for single projects


# Directories to skip when scanning for workspaces.
_SKIP_DIRS = frozenset({
    "node_modules", "dist", "build", "__pycache__",
    ".akemi", "venv", ".venv",
})

# Manifest files that indicate a project root.
_MANIFEST_FILES = (
    "package.json",
    "pyproject.toml",
    "go.mod",
    "Cargo.toml",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "requirements.txt",
    "setup.py",
)


def _read_text(path: Path) -> str:
    """Read a file as UTF-8 text, returning empty string on any failure."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def detect(directory: str | Path) -> DetectionResult:
    """Detect language, framework, test framework, and package manager.

    Detection order (first match wins for *language*):
      1. tsconfig.json          -> typescript
      2. package.json           -> javascript
      3. pyproject.toml / setup.py / requirements.txt -> python
      4. go.mod                 -> go
      5. Cargo.toml             -> rust
      6. pom.xml / build.gradle / build.gradle.kts -> java/kotlin
      7. *.csproj / *.sln       -> csharp

    Within each language block, framework / test-framework / package-manager are
    detected by grepping the relevant manifest contents.
    """
    d = Path(directory)
    lang = ""
    framework = ""
    test_fw = ""
    pkg_mgr = ""

    # ------------------------------------------------------------------
    # TypeScript / JavaScript
    # ------------------------------------------------------------------
    if (d / "tsconfig.json").is_file():
        lang = "typescript"
    elif (d / "package.json").is_file():
        lang = "javascript"

    if (d / "package.json").is_file():
        pkg_text = _read_text(d / "package.json")

        # Package manager (lockfile-based)
        if (d / "bun.lockb").is_file() or (d / "bun.lock").is_file():
            pkg_mgr = "bun"
        elif (d / "pnpm-lock.yaml").is_file():
            pkg_mgr = "pnpm"
        elif (d / "yarn.lock").is_file():
            pkg_mgr = "yarn"
        else:
            pkg_mgr = pkg_mgr or "npm"

        # Framework detection (first match wins)
        _js_frameworks = (
            ('"next"', "nextjs"),
            ('"@nestjs/core"', "nestjs"),
            ('"express"', "express"),
            ('"fastify"', "fastify"),
            ('"react"', "react"),
            ('"vue"', "vue"),
            ('"svelte"', "svelte"),
            ('"angular"', "angular"),
        )
        for needle, fw_name in _js_frameworks:
            if needle in pkg_text:
                framework = framework or fw_name
                break

        # Test framework detection
        _js_test_frameworks = (
            ('"vitest"', "vitest"),
            ('"jest"', "jest"),
            ('"mocha"', "mocha"),
        )
        for needle, tf_name in _js_test_frameworks:
            if needle in pkg_text:
                test_fw = test_fw or tf_name
                break

    # ------------------------------------------------------------------
    # Python
    # ------------------------------------------------------------------
    has_pyproject = (d / "pyproject.toml").is_file()
    has_setup_py = (d / "setup.py").is_file()
    has_requirements = (d / "requirements.txt").is_file()

    if has_pyproject or has_setup_py or has_requirements:
        lang = lang or "python"
        pkg_mgr = pkg_mgr or "pip"

        if has_pyproject:
            pyproj = _read_text(d / "pyproject.toml")

            # Framework
            if "fastapi" in pyproj:
                framework = framework or "fastapi"
            elif "django" in pyproj:
                framework = framework or "django"
            elif "flask" in pyproj:
                framework = framework or "flask"

            # Test framework
            if "pytest" in pyproj:
                test_fw = test_fw or "pytest"

            # Package manager refinement
            if "poetry" in pyproj:
                pkg_mgr = "poetry"
            elif (d / "uv.lock").is_file():
                pkg_mgr = "uv"

        # Also check requirements.txt for framework / test detection
        if has_requirements:
            reqs = _read_text(d / "requirements.txt").lower()
            if not framework or framework == "unknown":
                if "fastapi" in reqs:
                    framework = "fastapi"
                elif "django" in reqs:
                    framework = "django"
                elif "flask" in reqs:
                    framework = "flask"
            if not test_fw or test_fw == "unknown":
                if "pytest" in reqs:
                    test_fw = "pytest"

    # ------------------------------------------------------------------
    # Go
    # ------------------------------------------------------------------
    if (d / "go.mod").is_file():
        lang = lang or "go"
        pkg_mgr = pkg_mgr or "go"
        test_fw = test_fw or "go-test"

        go_mod = _read_text(d / "go.mod")
        if "gin-gonic" in go_mod:
            framework = framework or "gin"
        elif "labstack/echo" in go_mod:
            framework = framework or "echo"
        elif "gofiber" in go_mod:
            framework = framework or "fiber"

    # ------------------------------------------------------------------
    # Rust
    # ------------------------------------------------------------------
    if (d / "Cargo.toml").is_file():
        lang = lang or "rust"
        pkg_mgr = pkg_mgr or "cargo"
        test_fw = test_fw or "cargo-test"

        cargo = _read_text(d / "Cargo.toml")
        if "actix-web" in cargo:
            framework = framework or "actix"
        elif "axum" in cargo:
            framework = framework or "axum"
        elif "rocket" in cargo:
            framework = framework or "rocket"

    # ------------------------------------------------------------------
    # Java / Kotlin
    # ------------------------------------------------------------------
    has_pom = (d / "pom.xml").is_file()
    has_gradle = (d / "build.gradle").is_file()
    has_gradle_kts = (d / "build.gradle.kts").is_file()

    if has_pom or has_gradle or has_gradle_kts:
        if has_gradle_kts:
            lang = lang or "kotlin"
        else:
            lang = lang or "java"

        if has_pom:
            pkg_mgr = pkg_mgr or "maven"
        else:
            pkg_mgr = pkg_mgr or "gradle"

        test_fw = test_fw or "junit"
        framework = framework or "spring"

    # ------------------------------------------------------------------
    # C# / .NET
    # ------------------------------------------------------------------
    has_csproj = any(d.glob("*.csproj"))
    has_sln = any(d.glob("*.sln"))

    if has_csproj or has_sln:
        lang = lang or "csharp"
        pkg_mgr = pkg_mgr or "dotnet"
        test_fw = test_fw or "xunit"
        framework = framework or "aspnet"

    return DetectionResult(
        language=lang or "unknown",
        framework=framework or "unknown",
        test_framework=test_fw or "unknown",
        package_manager=pkg_mgr or "unknown",
    )


def detect_workspaces(directory: str | Path) -> ProjectInfo:
    """Detect monorepo structure by probing immediate subdirectories.

    Scans each subdirectory for manifest files.  If 2+ subdirectories
    resolve to different (non-unknown) language stacks, the project is
    classified as a monorepo.  Otherwise it is a single project.

    Skips hidden directories (starting with ``'.'``) and common
    non-project directories (node_modules, dist, build, __pycache__,
    .akemi, venv, .venv).
    """
    d = Path(directory)
    workspaces: list[WorkspaceInfo] = []

    if not d.is_dir():
        return ProjectInfo(
            type="single",
            workspaces=[],
            detection=detect(d),
        )

    for child in sorted(d.iterdir()):
        if not child.is_dir():
            continue

        name = child.name

        # Skip hidden and known non-project directories
        if name.startswith(".") or name in _SKIP_DIRS:
            continue

        # Check for at least one manifest file
        has_manifest = any((child / mf).is_file() for mf in _MANIFEST_FILES)
        if not has_manifest:
            continue

        result = detect(child)
        if result.language != "unknown":
            workspaces.append(WorkspaceInfo(
                name=name,
                root=f"{name}/",
                detection=result,
            ))

    root_detection = detect(d)

    if len(workspaces) >= 2:
        return ProjectInfo(
            type="monorepo",
            workspaces=workspaces,
            detection=root_detection,
        )

    return ProjectInfo(
        type="single",
        workspaces=[],
        detection=root_detection,
    )
