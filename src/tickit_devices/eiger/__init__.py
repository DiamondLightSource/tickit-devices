import pydantic.v1.dataclasses
from tickit.adapters.io import HttpIo, ZeroMqPushIo
from tickit.core.adapter import AdapterContainer
from tickit.core.components.component import Component, ComponentConfig
from tickit.core.components.device_component import DeviceComponent

from tickit_devices.eiger.eiger import EigerDevice
from tickit_devices.eiger.eiger_adapters import EigerRESTAdapter, EigerZMQAdapter


@pydantic.v1.dataclasses.dataclass
class Eiger(ComponentConfig):
    """Eiger simulation with HTTP adapter."""

    host: str = "0.0.0.0"
    port: int = 8081
    zmq_host: str = "127.0.0.1"
    zmq_port: int = 9999

    def __call__(self) -> Component:  # noqa: D102
        device = EigerDevice()
        adapters = [
            AdapterContainer(
                EigerRESTAdapter(device),
                HttpIo(
                    self.host,
                    self.port,
                ),
            ),
            AdapterContainer(
                EigerZMQAdapter(device),
                ZeroMqPushIo(
                    self.zmq_host,
                    self.zmq_port,
                ),
            ),
        ]
        return DeviceComponent(
            name=self.name,
            device=device,
            adapters=adapters,
        )
