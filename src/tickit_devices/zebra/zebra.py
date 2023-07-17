from typing import Dict

from tickit.adapters.composed import ComposedAdapter
from tickit.adapters.interpreters.command import RegexCommand
from tickit.adapters.servers.tcp import TcpServer
from tickit.core.components.system_simulation import SystemSimulationComponent
from tickit.core.typedefs import ComponentID

from tickit_devices.zebra._common import Block, mux_types, param_types, register_names
from tickit_devices.zebra.and_or_block import AndOrBlockConfig


class ZebraDevice(SystemSimulationComponent):
    blocks = Dict[str, Block]
    params: Dict[str, int]
    muxes: Dict[str, int]
    server: TcpServer

    def __init__(self, name: ComponentID, host: str = "localhost", port: int = 7012):
        self.params = {param: 0 for param in param_types}
        self.muxes = {mux: 0 for mux in mux_types}
        self.blocks = {
            block.name: block
            for block in [
                AndOrBlockConfig(ComponentID(f"{ANDOR}{NUM + 1}"), self.params)
                for ANDOR in {"AND", "OR"}
                for NUM in range(4)
            ]
        }
        self.server = TcpServer(host, port)
        super().__init__(
            name=name,
            expose={},
            components=[block for block in self.blocks.values()],
        )

    def set_reg(self, reg: int, value: int):
        reg_name = register_names[reg]
        if reg_name in self.params:
            self.params[reg_name] = value
            for block_name in param_types[reg_name].blocks:
                self.components[block_name].raise_interrupt()
        else:
            self.muxes[reg_name] = value

    def get_reg(self, reg: int) -> int:
        reg_name = register_names[reg]
        try:
            return self.params[reg_name]
        except KeyError:
            return self.muxes[reg_name]


class ZebraAdapter(ComposedAdapter[bytes, ZebraDevice]):
    """network adapter for zebra system simulation"""

    @RegexCommand(rb"W([0-9A-F]{2})([0-9A-F]{4})\n", interrupt=True)
    async def set_reg(self, reg: str, value: str) -> bytes:
        reg_int, value_int = int(reg, base=16), int(value, base=16)
        self.device.set_reg(reg_int, value_int)
        return b"W%02XOK" % reg_int

    @RegexCommand(rb"R([0-9A-F]{2})\n")
    async def get_reg(self, reg: str) -> bytes:
        reg_int = int(reg, base=16)
        value_int = self.device.get_reg(reg_int)
        return b"R%02X%04XOK" % (reg_int, value_int)
