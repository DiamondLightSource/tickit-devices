import pydantic.v1.dataclasses
from tickit.core.components.component import Component, ComponentConfig
from tickit.core.components.device_simulation import DeviceSimulation

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
        return DeviceSimulation(
            name=self.name,
            device=EigerDevice(),
            adapters=[
                EigerRESTAdapter(host=self.host, port=self.port),
                EigerZMQAdapter(host=self.zmq_host, port=self.zmq_port),
            ],
        )
