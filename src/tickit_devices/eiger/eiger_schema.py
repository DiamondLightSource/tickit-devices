import logging
from enum import Enum
from functools import partial
from typing import Any, Generic, List, Mapping, Optional, TypeVar

from pydantic.v1 import BaseModel, Field

T = TypeVar("T")

LOGGER = logging.getLogger(__name__)


def field_config(**kwargs) -> Mapping[str, Any]:
    """Helper function to create a typesafe dictionary.

    Helper function to create a typesafe dictionary to be inserted as
    dataclass metadata.

    Args:
        kwargs: Key/value pairs to go into the metadata

    Returns:
        Mapping[str, Any]: A dictionary of {key: value} where all keys are strings
    """
    return dict(**kwargs)


class AccessMode(Enum):
    """Possible access modes for field metadata."""

    READ_ONLY: str = "r"
    WRITE_ONLY: str = "w"
    READ_WRITE: str = "rw"
    NONE: str = "None"


class ValueType(Enum):
    """Possible value types for field metadata."""

    FLOAT: str = "float"
    INT: str = "int"
    UINT: str = "uint"
    STRING: str = "string"
    STR_LIST: str = "string[]"
    BOOL: str = "bool"
    FLOAT_GRID: str = "float[][]"
    UINT_GRID: str = "uint[][]"
    DATE: str = "date"
    DATETIME: str = "datetime"
    NONE: str = "none"
    STATE: str = "State"


#
# Shortcuts to creating dataclass field metadata
#
rw_float: partial = partial(
    field_config, value_type=ValueType.FLOAT, access_mode=AccessMode.READ_WRITE
)
ro_float: partial = partial(
    field_config, value_type=ValueType.FLOAT, access_mode=AccessMode.READ_ONLY
)
rw_int: partial = partial(
    field_config, value_type=ValueType.INT, access_mode=AccessMode.READ_WRITE
)
ro_int: partial = partial(
    field_config, value_type=ValueType.INT, access_mode=AccessMode.READ_ONLY
)
rw_uint: partial = partial(
    field_config, value_type=ValueType.UINT, access_mode=AccessMode.READ_WRITE
)
rw_str: partial = partial(
    field_config, value_type=ValueType.STRING, access_mode=AccessMode.READ_WRITE
)
ro_str: partial = partial(
    field_config, value_type=ValueType.STRING, access_mode=AccessMode.READ_ONLY
)
rw_bool: partial = partial(
    field_config, value_type=ValueType.BOOL, access_mode=AccessMode.READ_WRITE
)
rw_float_grid: partial = partial(
    field_config,
    value_type=ValueType.FLOAT_GRID,
    access_mode=AccessMode.READ_WRITE,
)
rw_uint_grid: partial = partial(
    field_config,
    value_type=ValueType.UINT_GRID,
    access_mode=AccessMode.READ_WRITE,
)
ro_date: partial = partial(
    field_config, value_type=ValueType.DATE, access_mode=AccessMode.READ_ONLY
)
rw_datetime: partial = partial(
    field_config, value_type=ValueType.DATETIME, access_mode=AccessMode.READ_WRITE
)
rw_state: partial = partial(
    field_config, value_type=ValueType.STATE, access_mode=AccessMode.READ_WRITE
)
ro_str_list: partial = partial(
    field_config, value_type=ValueType.STR_LIST, access_mode=AccessMode.READ_ONLY
)


class Value(BaseModel, Generic[T]):
    """Schema for a value to be returned by the API. Most fields are optional."""

    value: T
    value_type: str
    access_mode: Optional[AccessMode] = None
    unit: Optional[str] = None
    min: Optional[T] = None
    max: Optional[T] = None
    allowed_values: Optional[List[str]] = None


def construct_value(obj, param):  # noqa: D103
    value = obj[param]["value"]
    meta = obj[param]["metadata"]

    if "allowed_values" in meta:
        data = Value(
            value=value,
            value_type=meta["value_type"].value,
            access_mode=meta["access_mode"].value,
            allowed_values=meta["allowed_values"],
        ).dict()

    else:
        data = Value(
            value=value,
            value_type=meta["value_type"].value,
            access_mode=meta["access_mode"].value,
        ).dict()

    return data


class SequenceComplete(BaseModel):
    """Schema for confirmation returned by operations that do not return values."""

    sequence_id: int = Field(default=1, alias="sequence id")

    @classmethod
    def number(cls, number: int) -> "SequenceComplete":
        """Create a new completion document with the given ID.

        This function exists as a workaround for mypy ignoring aliases.
        See https://github.com/pydantic/pydantic/discussions/2889

        Args:
            number: The sequence ID

        Returns:
            SequenceComplete: Document describing a completed sequence of operations
        """
        return SequenceComplete(sequence_id=number)  # type: ignore

    class Config:
        allow_population_by_field_name = True
