"""Read the YAML configuration file."""

from __future__ import annotations

from types import MappingProxyType

import yaml

from skyweaver.model.configuration import ConfigPath, Configuration


def load_configuration(config_path: ConfigPath) -> Configuration:
    """Parse the configuration file; relative paths resolve against its folder."""

    path = config_path.path.resolve()
    with open(path, "r") as file:
        data = yaml.safe_load(file) or {}
    return Configuration(fields=MappingProxyType(data), config_dir=path.parent)
