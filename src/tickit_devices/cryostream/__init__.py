import pydantic.v1.dataclasses
from tickit.adapters.io import TcpIo
from tickit.core.adapter import AdapterContainer
from tickit.core.components.component import Component, ComponentConfig
from tickit.core.components.device_component import DeviceComponent

from .cryostream import CryostreamAdapter, CryostreamDevice


@pydantic.v1.dataclasses.dataclass
class Cryostream(ComponentConfig):
    """Cryostream simulation with TCP server."""

    host: str = "localhost"
    port: int = 25565

    def __call__(self) -> Component:  # noqa: D102
        device = CryostreamDevice()
        adapters = [
            AdapterContainer(
                CryostreamAdapter(device),
                TcpIo(
                    self.host,
                    self.port,
                ),
            )
        ]
        return DeviceComponent(
            name=self.name,
            device=device,
            adapters=adapters,
        )
