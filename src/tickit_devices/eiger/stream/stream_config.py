from dataclasses import dataclass, field, fields
from typing import Any

from tickit_devices.eiger.eiger_schema import rw_str


def stream_config_keys() -> list[str]:
    return ["format", "header_appendix", "header_detail", "image_appendix", "mode"]


LEGACY_STREAM = "legacy"
CBOR_STREAM = "cbor"


@dataclass
class StreamConfig:
    """Eiger stream configuration taken from the API spec."""

    mode: str = field(
        default="enabled", metadata=rw_str(allowed_values=["enabled", "disabled"])
    )
    format: str = field(
        default=LEGACY_STREAM,
        metadata=rw_str(allowed_values=[LEGACY_STREAM, CBOR_STREAM]),
    )
    header_detail: str = field(
        default="basic", metadata=rw_str(allowed_values=["none", "basic", "all"])
    )
    header_appendix: str = field(default="", metadata=rw_str())
    image_appendix: str = field(default="", metadata=rw_str())

    keys: list[str] = field(default_factory=stream_config_keys)

    def __getitem__(self, key: str) -> Any:  # noqa: D105
        for field_ in fields(self):
            if field_.name == key:
                return {"value": vars(self)[field_.name], "metadata": field_.metadata}
        raise ValueError(f"No field with name {key}")

    def __setitem__(self, key: str, value: Any) -> None:  # noqa: D105
        self.__dict__[key] = value
