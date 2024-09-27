import pydantic.v1.dataclasses
from tickit.adapters.io import TcpIo
from tickit.core.adapter import AdapterContainer
from tickit.core.components.component import Component, ComponentConfig
from tickit.core.components.device_component import DeviceComponent

from .digitelmpc import DigitelMpcAdapter, DigitelMpcDevice


@pydantic.v1.dataclasses.dataclass
class DigitelMpc(ComponentConfig):
    """DigitelMpc simulation with TCP server."""

    host: str = "localhost"
    port: int = 25565

    def __call__(self) -> Component:  # noqa: D102
        device = DigitelMpcDevice()
        adapters = [
            AdapterContainer(
                DigitelMpcAdapter(device),
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