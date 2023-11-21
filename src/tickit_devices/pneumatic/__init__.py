import pydantic.v1.dataclasses
from tickit.adapters.io import EpicsIo
from tickit.core.adapter import AdapterContainer
from tickit.core.components.component import Component, ComponentConfig
from tickit.core.components.device_component import DeviceComponent

from .pneumatic import PneumaticAdapter, PneumaticDevice


@pydantic.v1.dataclasses.dataclass
class Pneumatic(ComponentConfig):
    """Pneumatic simulation with EPICS IOC adapter."""

    initial_speed: float = 2.5
    initial_state: bool = False
    db_file: str = "src/tickit_devices/pneumatic/db_files/filter1.db"
    ioc_name: str = "PNEUMATIC"

    def __call__(self) -> Component:  # noqa: D102
        device = PneumaticDevice(
            initial_speed=self.initial_speed, initial_state=self.initial_state
        )
        adapters = [
            AdapterContainer(
                PneumaticAdapter(device),
                EpicsIo(
                    self.ioc_name,
                    self.db_file,
                ),
            )
        ]
        return DeviceComponent(
            name=self.name,
            device=device,
            adapters=adapters,
        )
