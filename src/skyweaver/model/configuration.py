"""The configuration file and its contents."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any


@dataclass(frozen=True)
class ConfigPath:
    """The path of the YAML configuration file."""

    path: Path


@dataclass(frozen=True)
class Configuration:
    """The parsed YAML configuration and the directory it was read from.

    Relative paths inside the configuration are resolved against
    `config_dir`. `fields` is a read-only view of the parsed document.
    """

    fields: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    config_dir: Path = field(default_factory=Path.cwd)
