from dataclasses import dataclass, field, fields
from typing import Any

from tickit_devices.eiger.eiger_schema import ro_int, ro_str, ro_str_list, ro_uint


def monitor_status_keys() -> list[str]:
    return ["buffer_free", "dropped", "error", "state"]


@dataclass
class MonitorStatus:
    """Eiger monitor status taken from the API spec."""

    error: list[str] = field(default_factory=lambda: [], metadata=ro_str())
    buffer_fill_level: int = field(default=2, metadata=ro_int())
    buffer_free: int = field(default_factory=int, metadata=ro_uint())
    dropped: int = field(default=0, metadata=ro_uint())
    state: str = field(
        default="normal", metadata=ro_str(allowed_values=["normal", "overflow"])
    )
    keys: list[str] = field(default_factory=monitor_status_keys, metadata=ro_str_list())

    def __getitem__(self, key: str) -> Any:  # noqa: D105
        for field_ in fields(self):
            if field_.name == key:
                return {"value": vars(self)[field_.name], "metadata": field_.metadata}
        raise ValueError(f"No field with name {key}")
