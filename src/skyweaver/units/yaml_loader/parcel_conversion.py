"""Conversions between the old parcels and the new values (removed with the old core)."""

from types import MappingProxyType

from skyweaver.model.configuration import Configuration
from skyweaver.units.yaml_loader.logistics.yaml_parcel import YAMLParcel


def configuration_of(parcel: YAMLParcel) -> Configuration:
    return Configuration(
        fields=MappingProxyType(parcel.yaml_fields), config_dir=parcel.config_dir
    )
