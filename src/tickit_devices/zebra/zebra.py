import asyncio
from typing import Dict, Optional, Union

from tickit.adapters.specifications import RegexCommand
from tickit.adapters.system import BaseSystemSimulationAdapter
from tickit.core.components.device_simulation import DeviceSimulation
from tickit.core.management.event_router import InverseWiring, Wiring
from tickit.core.typedefs import ComponentID

from tickit_devices.zebra._common import (
    Block,
    Mux,
    mux_types,
    param_types,
    register_names,
)


class ZebraAdapter(BaseSystemSimulationAdapter):
    _components: Dict[ComponentID, DeviceSimulation]
    params: dict[str, int]
    """
    Network adapter for a Zebra system simulation, which operates a TCP server for
    reading and writing params (configuration of the internal blocks) and muxes
    (state of the internal blocks).

    Attempting to set or read muxes from blocks that are not instantiated returns 0.

    Params that are currently supported:
    - For AND/OR gates N=1,2,3,4, the following (default 0) may be set
    to Σ2**M where M is each input (1,2,3,4) for which the behaviour is desired.
    {AND|OR}{N}_INV: Inverts input(s) M
    {AND|OR}{N}_ENA: Enables input(s) M

    Muxes that are currently supported:
    The following values may also be read from or set on the register of the blocks:
    - For AND/OR gates N=1,2,3,4, for inputs M=1,2,3,4
    {AND|OR}{N}_INP{M}
    """

    def __init__(self, params: dict[str, int]):
        self.params = params

    def setup_adapter(
        self,
        components: Dict[ComponentID, DeviceSimulation],
        wiring: Union[Wiring, InverseWiring],
    ) -> None:
        """
        Sets the shared configuration/"params" between the Zebra and its components
        then instantiates them.
        """
        for block in components.values():
            block.device.params = self.params
        super().setup_adapter(components, wiring)

    @RegexCommand(rb"W([0-9A-F]{2})([0-9A-F]{4})\n", interrupt=True)
    async def set_reg(self, reg: str, value: str) -> bytes:
        reg_int, value_int = int(reg, base=16), int(value, base=16)
        reg_name = register_names[reg_int]

        if reg_name in self.params:
            self.params[reg_name] = value_int

            for block_name in param_types[reg_name].blocks:
                await asyncio.create_task(
                    self._components[block_name].raise_interrupt()
                )

        else:
            self._set_mux(reg_name, value_int)

        return b"W%02XOK" % reg_int

    @RegexCommand(rb"R([0-9A-F]{2})\n")
    async def get_reg(self, reg: str) -> bytes:
        reg_int = int(reg, base=16)
        reg_name = register_names[reg_int]
        try:
            value_int = self.params[reg_name]
        except KeyError:
            value_int = self._read_mux(reg_name)
        return b"R%02X%04XOK" % (reg_int, value_int)

    def _read_mux(self, reg_name: str) -> int:
        block = self._get_mux_block(reg_name)
        if block:
            return block.read_mux(reg_name.removeprefix(f"{block.name}_"))
        return 0

    def _set_mux(self, reg_name: str, value: int) -> int:
        block = self._get_mux_block(reg_name)
        if block:
            return block.set_mux(reg_name.removeprefix(f"{block.name}_"), value)
        return 0

    def _get_mux_block(self, reg_name: str) -> Optional[Block]:
        register: Mux = mux_types[reg_name]
        if not register:
            return None
        block_name = register.block
        if not block_name:
            return None
        block = self._components.get(ComponentID(block_name))
        if not isinstance(block, Block):
            return None
        return block
