from pathlib import Path

from skyweaver.core.operations.operational_unit import OperationalUnit
from skyweaver.model.configuration import ConfigPath
from skyweaver.units.yaml_loader.configuration import load_configuration
from skyweaver.units.yaml_loader.logistics.yaml_outpost import YAMLOutpost
from skyweaver.units.yaml_loader.logistics.yaml_parcel import YAMLParcel


class YAMLLoaderUnit(OperationalUnit[YAMLOutpost]):

    def __init__(self, yaml_path: str, outpost=None):
        self._yaml_path = yaml_path
        super().__init__(outpost or YAMLOutpost())

    def run(self):

        configuration = load_configuration(ConfigPath(Path(self._yaml_path)))

        with self._outpost:
            self._outpost.yaml_parcel = YAMLParcel(
                yaml_fields=dict(configuration.fields),
                config_dir=configuration.config_dir,
            )
