from dataclasses import dataclass, field, fields
from typing import Any

from tickit_devices.eiger.eiger_schema import ro_str_list, rw_bool, rw_str, rw_uint


def monitor_config_keys() -> list[str]:
    return ["buffer_size", "discard_new", "mode"]


@dataclass
class MonitorConfig:
    """Eiger monitor configuration taken from the API spec."""

    mode: str = field(
        default="enabled", metadata=rw_str(allowed_values=["enabled", "disabled"])
    )
    buffer_size: int = field(default=512, metadata=rw_uint())
    discard_new: bool = field(default=False, metadata=rw_bool())

    keys: list[str] = field(default_factory=monitor_config_keys, metadata=ro_str_list())

    def __getitem__(self, key: str) -> Any:  # noqa: D105
        for field_ in fields(self):
            if field_.name == key:
                return {"value": vars(self)[field_.name], "metadata": field_.metadata}
        raise ValueError(f"No field with name {key}")

    def __setitem__(self, key: str, value: Any) -> None:  # noqa: D105
        self.__dict__[key] = value
