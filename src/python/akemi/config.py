"""Read and write ``akemi.yaml`` project configuration.

The configuration file lives at ``.akemi/akemi.yaml`` inside a
project root and describes the project type, language stack, and
(for monorepos) workspace layout.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from . import yaml_io

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class WorkspaceConfig:
    """Configuration for a single workspace inside a monorepo."""

    root: str
    language: str
    framework: str = "unknown"
    test_framework: str = "unknown"
    package_manager: str = "unknown"

    def to_dict(self) -> dict[str, str]:
        return {
            "root": self.root,
            "language": self.language,
            "framework": self.framework,
            "test_framework": self.test_framework,
            "package_manager": self.package_manager,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkspaceConfig":
        return cls(
            root=str(data.get("root", "")),
            language=str(data.get("language", "")),
            framework=str(data.get("framework", "unknown")),
            test_framework=str(data.get("test_framework", "unknown")),
            package_manager=str(data.get("package_manager", "unknown")),
        )


@dataclass
class AkemiConfig:
    """Top-level Akemi project configuration."""

    name: str = ""
    type: str = "single"  # "single" or "monorepo"
    language: str = ""
    framework: str = ""
    test_framework: str = ""
    package_manager: str = ""
    workspaces: dict[str, WorkspaceConfig] = field(default_factory=dict)

    # Sections this class does not manage but must preserve on round-trip
    # (agents, graph, standards, etc.).
    _extra_sections: dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    @classmethod
    def from_file(cls, filepath: str | Path) -> "AkemiConfig":
        """Read an ``akemi.yaml`` file and return an :class:`AkemiConfig`."""
        filepath = Path(filepath)
        raw = filepath.read_text(encoding="utf-8")
        data: dict[str, Any] = yaml_io.safe_load(raw) or {}
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AkemiConfig":
        """Construct from a parsed YAML dict.

        The file format nests project fields under a ``project:`` key,
        but we flatten them into top-level config attributes for ease of
        use.  Sections not managed by this class (``agents``, ``graph``,
        ``standards``, etc.) are preserved verbatim for round-tripping.
        """
        project: dict[str, Any] = data.get("project") or {}

        # Parse workspaces
        raw_ws: dict[str, Any] = data.get("workspaces") or {}
        workspaces: dict[str, WorkspaceConfig] = {}
        for ws_name, ws_data in raw_ws.items():
            if isinstance(ws_data, dict):
                workspaces[ws_name] = WorkspaceConfig.from_dict(ws_data)

        # Preserve sections we don't manage.
        _MANAGED_KEYS = {"akemi", "project", "workspaces"}
        extra = {k: v for k, v in data.items() if k not in _MANAGED_KEYS}

        cfg = cls(
            name=str(project.get("name", "")),
            type=str(project.get("type", "single")),
            language=str(project.get("language", "")),
            framework=str(project.get("framework", "")),
            test_framework=str(project.get("test_framework", "")),
            package_manager=str(project.get("package_manager", "")),
            workspaces=workspaces,
        )
        cfg._extra_sections = extra
        return cfg

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Return a dict matching the ``akemi.yaml`` file layout.

        Preserves unmanaged sections (``agents``, ``graph``, ``standards``,
        etc.) that were present when the config was loaded.
        """
        d: dict[str, Any] = {
            "akemi": "v1",
            "project": {
                "name": self.name,
                "type": self.type,
                "language": self.language,
                "framework": self.framework,
                "test_framework": self.test_framework,
                "package_manager": self.package_manager,
            },
        }
        if self.workspaces:
            d["workspaces"] = {
                name: ws.to_dict() for name, ws in self.workspaces.items()
            }
        # Re-attach preserved sections.
        d.update(self._extra_sections)
        return d

    def to_file(self, filepath: str | Path) -> None:
        """Write the configuration to an ``akemi.yaml`` file."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        content = yaml.dump(
            self.to_dict(),
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            width=200,
        )
        filepath.write_text(content, encoding="utf-8")

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    @property
    def is_monorepo(self) -> bool:
        return self.type == "monorepo"

    def workspace_for_path(self, filepath: str) -> str:
        """Return the workspace name whose root is a prefix of
        *filepath*, or ``'default'`` if no workspace matches."""
        for ws_name, ws_cfg in self.workspaces.items():
            if filepath.startswith(ws_cfg.root):
                return ws_name
        return "default"
