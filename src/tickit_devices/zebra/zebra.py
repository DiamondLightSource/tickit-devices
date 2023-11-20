import asyncio
from typing import Dict, Union

from tickit.adapters.specifications import RegexCommand
from tickit.adapters.system import BaseSystemSimulationAdapter
from tickit.core.components.device_component import DeviceComponent
from tickit.core.management.event_router import InverseWiring, Wiring
from tickit.core.typedefs import ComponentID

from tickit_devices.zebra._common import param_types, register_names


class ZebraAdapter(BaseSystemSimulationAdapter):
    _components: Dict[ComponentID, DeviceComponent]
    params: dict[str, int]
    """
    Network adapter for a Zebra system simulation, which operates a TCP server for
    reading and setting configuration of blocks and internal wiring mapping.
    N.B. Reading and setting internal wiring is not currently supported,and all
    "mux" related queries will return as though successful but not operate.

    See documentation for the Zebra:
    `https://github.com/dls-controls/zebra/blob/master/documentation/TDI-CTRL-TNO-042-Zebra-Manual.pdf`

    Configuration that is currently supported:
    - For AND/OR gates N=1,2,3,4, the following (default 0) may be set
    to Σ2**M where M is each input (1,2,3,4) for which the behaviour is desired.
    {AND|OR}{N}_INV: Inverts input(s) M
    {AND|OR}{N}_ENA: Enables input(s) M
    """

    def __init__(self, params: dict[str, int]):
        self.params = params

    def setup_adapter(
        self,
        components: Dict[ComponentID, DeviceComponent],
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

    def _read_mux(self, reg_name: str) -> int:  # type: ignore
        # TODO: Support reading Muxes: map internal wiring into Mux values
        return 0

    def _set_mux(self, reg_name: str, value: int) -> int:  # type: ignore
        # TODO: Support setting Muxes: map Mux value into internal wiring
        # TODO: Support cyclic wirings involving Zebra: AND1_OUT->AND1_INP1 is valid
        return 0
