import pydantic.v1.dataclasses

from tickit.core.components.component import Component
from tickit.core.components.system_simulation import SystemSimulation

from tickit_devices.zebra.zebra import ZebraDevice


@pydantic.v1.dataclasses.dataclass
class Zebra(SystemSimulation):
    """Zebra simulation with TCP server."""

    host: str = "localhost"
    port: int = 7012

    def __call__(self) -> Component:  # noqa: D102
        return ZebraDevice(
            name=self.name,
            host=self.host,
            port=self.port,
        )
