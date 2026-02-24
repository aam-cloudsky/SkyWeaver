from dataclasses import dataclass, fields, MISSING, is_dataclass
from typing import Any, ClassVar, Dict, Type, TypeVar, Union, get_origin, get_args, cast
from enum import Enum

from skyweaver.units.yaml_loader.logistics.yaml_parcel import YAMLParcel

T = TypeVar("T", bound="BaseParameters")


class BaseParameters:
    yaml_section: ClassVar[str]

    @classmethod
    def from_yaml_parcel(cls: Type[T], parcel: YAMLParcel) -> T:

        if not hasattr(cls, "yaml_section") or not cls.yaml_section:
            raise ValueError(f"{cls.__name__} must define 'yaml_section'")

        if not is_dataclass(cls):
            raise TypeError(f"{cls.__name__} must be a dataclass")

        raw: Dict[str, Any] = parcel.yaml_fields.get(cls.yaml_section, {}) or {}
        kwargs: Dict[str, Any] = {}

        dataclass_cls = cast(Type[Any], cls)

        for f in fields(dataclass_cls):

            if f.name in raw:
                value = raw[f.name]
                field_type = f.type
                origin = get_origin(field_type)

                # --------------------------------------------------
                # Handle Optional[...] (Union[..., None])
                # --------------------------------------------------
                if origin is Union:
                    args = get_args(field_type)

                    # Detect Enum inside Optional
                    enum_types = [
                        a for a in args if isinstance(a, type) and issubclass(a, Enum)
                    ]

                    if enum_types:
                        enum_cls = enum_types[0]

                        if value is not None:
                            if not isinstance(value, str):
                                raise TypeError(
                                    f"Field '{f.name}' must be a string "
                                    f"representing {enum_cls.__name__} member name."
                                )

                            try:
                                value = enum_cls[value]
                            except KeyError:
                                valid = ", ".join(enum_cls.__members__.keys())
                                raise ValueError(
                                    f"Invalid value '{value}' for enum "
                                    f"{enum_cls.__name__}. Valid options: {valid}"
                                )

                # --------------------------------------------------
                # Handle direct Enum
                # --------------------------------------------------
                elif isinstance(field_type, type) and issubclass(field_type, Enum):

                    if not isinstance(value, str):
                        raise TypeError(
                            f"Field '{f.name}' must be a string "
                            f"representing {field_type.__name__} member name."
                        )

                    try:
                        value = field_type[value]
                    except KeyError:
                        valid = ", ".join(field_type.__members__.keys())
                        raise ValueError(
                            f"Invalid value '{value}' for enum "
                            f"{field_type.__name__}. Valid options: {valid}"
                        )

                kwargs[f.name] = value

            elif f.default is not MISSING:
                kwargs[f.name] = f.default

            elif f.default_factory is not MISSING:  # type: ignore
                kwargs[f.name] = f.default_factory()

            else:
                raise KeyError(f"Missing required key '{cls.yaml_section}.{f.name}'")

        return cls(**kwargs)
