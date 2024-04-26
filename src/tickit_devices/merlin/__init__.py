import pydantic.v1.dataclasses
from tickit.adapters.io import TcpIo, ZeroMqPushIo
from tickit.core.adapter import AdapterContainer
from tickit.core.components.component import Component, ComponentConfig
from tickit.core.components.device_component import DeviceComponent

from tickit_devices.merlin.adapters import MerlinControlAdapter, MerlinDataAdapter
from tickit_devices.merlin.merlin import MerlinDetector
from tickit_devices.merlin.tcp import TcpPushIo


@pydantic.v1.dataclasses.dataclass
class Merlin(ComponentConfig):
    """Merlin simulation with TCP streams"""

    host: str = "127.0.0.1"
    ctrl_port: int = 6341
    data_port: int = 6342

    def __call__(self) -> Component:  # noqa: D102
        detector = MerlinDetector()
        data_adapter = MerlinDataAdapter(detector)
        control_adapter = MerlinControlAdapter(detector, data_adapter)
        adapters = [
            AdapterContainer(data_adapter, TcpPushIo(self.host, self.data_port)),
            AdapterContainer(control_adapter, TcpIo(self.host, self.ctrl_port)),
        ]

        return DeviceComponent(name=self.name, device=detector, adapters=adapters)
