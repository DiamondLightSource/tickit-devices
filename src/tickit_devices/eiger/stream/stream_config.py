from dataclasses import dataclass, field, fields
from typing import Any

from tickit_devices.eiger.eiger_schema import ro_str_list, rw_str


def stream_config_keys() -> list[str]:
    return ["format", "header_appendix", "header_detail", "image_appendix", "mode"]


@dataclass
class StreamConfig:
    """Eiger stream configuration taken from the API spec."""

    mode: str = field(
        default="enabled", metadata=rw_str(allowed_values=["enabled", "disabled"])
    )
    header_detail: str = field(
        default="basic", metadata=rw_str(allowed_values=["none", "basic", "all"])
    )
    header_appendix: str = field(default="", metadata=rw_str())
    image_appendix: str = field(default="", metadata=rw_str())

    keys: list[str] = field(default_factory=stream_config_keys, metadata=ro_str_list())

    def __getitem__(self, key: str) -> Any:  # noqa: D105
        f = {}
        for field_ in fields(self):
            f[field_.name] = {
                "value": vars(self)[field_.name],
                "metadata": field_.metadata,
            }
        return f[key]

    def __setitem__(self, key: str, value: Any) -> None:  # noqa: D105
        self.__dict__[key] = value
