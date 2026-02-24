from skyweaver.core.operations.operational_unit import OperationalUnit
import yaml

from skyweaver.units.yaml_loader.logistics.yaml_outpost import YAMLOutpost
from skyweaver.units.yaml_loader.logistics.yaml_parcel import YAMLParcel


class YAMLLoaderUnit(OperationalUnit[YAMLOutpost]):

    def __init__(self, yaml_path: str, outpost=None):
        self._yaml_path = yaml_path
        super().__init__(outpost or YAMLOutpost())

    def run(self):

        with open(self._yaml_path, "r") as f:
            data = yaml.safe_load(f) or {}

            with self._outpost:
                self._outpost.yaml_parcel = YAMLParcel(yaml_fields=data)
