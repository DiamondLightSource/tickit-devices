"""Eiger_status temporary docstring - to be changed."""

from dataclasses import dataclass, field, fields
from datetime import datetime
from enum import Enum
from typing import Any

from .eiger_schema import ro_float, ro_str


class State(Enum):
    """Possible states of the Eiger detector."""

    NA = "na"
    IDLE = "idle"
    READY = "ready"
    ACQUIRE = "acquire"
    CONFIGURE = "configure"
    INITIALIZE = "initialize"
    ERROR = "error"
    # TEST = "test"


def status_keys() -> list[str]:
    return [
        # "error",  # Eiger does not report error as a key
        "humidity",
        "link_0",
        "link_1",
        "series_unique_id",
        "state",
        "temperature",
        "time",
    ]


@dataclass
class EigerStatus:
    """Stores the status parameters of the Eiger detector."""

    state: State = field(
        default=State.NA,
        metadata=ro_str(allowed_values=[state.value for state in State]),
    )
    error: list[str] = field(default_factory=list, metadata=ro_str())
    temperature: float = field(default=24.5, metadata=ro_float())
    humidity: float = field(default=0.2, metadata=ro_float())
    time: datetime = field(default=datetime.now(), metadata=ro_str())
    dcu_buffer_free: float = field(default=0.5, metadata=ro_float())
    link_0: str = field(default="up", metadata=ro_str(allowed_values=["up", "down"]))
    link_1: str = field(default="up", metadata=ro_str(allowed_values=["up", "down"]))
    series_unique_id: str = field(
        default="01HBV3JPF9T4ZDPADX6EMK6XMZ", metadata=ro_str()
    )

    keys: list[str] = field(default_factory=status_keys)

    def __getitem__(self, key: str) -> Any:  # noqa: D105
        for field_ in fields(self):
            if field_.name == key:
                return {"value": vars(self)[field_.name], "metadata": field_.metadata}
        raise ValueError(f"No field with name {key}")
