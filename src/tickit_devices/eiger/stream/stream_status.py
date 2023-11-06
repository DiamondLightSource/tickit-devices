from dataclasses import dataclass, field, fields
from typing import Any

from tickit_devices.eiger.eiger_schema import ro_str, ro_str_list, ro_uint


def stream_status_keys() -> list[str]:
    # Eiger does not report error as a key
    return ["dropped", "state"]


@dataclass
class StreamStatus:
    """Eiger stream status taken from the API spec."""

    state: str = field(
        default="ready",
        metadata=ro_str(allowed_values=["disabled", "ready", "acquire", "error"]),
    )
    error: list[str] = field(default_factory=lambda: [], metadata=ro_str())
    dropped: int = field(default=0, metadata=ro_uint())

    keys: list[str] = field(default_factory=stream_status_keys, metadata=ro_str_list())

    def __getitem__(self, key: str) -> Any:  # noqa: D105
        f = {}
        for field_ in fields(self):
            f[field_.name] = {
                "value": vars(self)[field_.name],
                "metadata": field_.metadata,
            }
        return f[key]
