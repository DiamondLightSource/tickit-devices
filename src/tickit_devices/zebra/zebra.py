import asyncio
from typing import Dict, Union

from tickit.adapters.specifications import RegexCommand
from tickit.adapters.system import BaseSystemSimulationAdapter
from tickit.core.components.device_simulation import DeviceSimulation
from tickit.core.management.event_router import InverseWiring, Wiring
from tickit.core.typedefs import ComponentID

from tickit_devices.zebra._common import param_types, register_names, Block


class ZebraAdapter(BaseSystemSimulationAdapter):
    _components: Dict[ComponentID, DeviceSimulation]
    params: dict[str, int]
    muxes: dict[str, int]
    """network adapter for zebra system simulation"""

    def __init__(self, params: dict[str, int], muxes: dict[str, int]):
        self.params = params
        self.muxes = muxes

    def setup_adapter(
        self,
        components: Dict[ComponentID, DeviceSimulation],
        wiring: Union[Wiring, InverseWiring],
    ) -> None:
        """Provides the components and wiring of a SystemSimulationComponent."""
        for block in components.values():
            block.device.params = self.params
        super().setup_adapter(components, wiring)

    @RegexCommand(rb"W([0-9A-F]{2})([0-9A-F]{4})\n", interrupt=True)
    async def set_reg(self, reg: str, value: str) -> bytes:
        reg_int, value_int = int(reg, base=16), int(value, base=16)
        reg_name = register_names[reg_int]

        if reg_name in self.params:
            self.params[reg_name] = value_int

            async with asyncio.TaskGroup() as tg:
                for block_name in param_types[reg_name].blocks:
                    tg.create_task(self._components[block_name].raise_interrupt())

        else:
            self.muxes[reg_name] = value_int

        return b"W%02XOK" % reg_int

    @RegexCommand(rb"R([0-9A-F]{2})\n")
    async def get_reg(self, reg: str) -> bytes:
        reg_int = int(reg, base=16)
        reg_name = register_names[reg_int]
        try:
            value_int = self.params[reg_name]
        except KeyError:
            value_int = self.muxes[reg_name]
        return b"R%02X%04XOK" % (reg_int, value_int)
