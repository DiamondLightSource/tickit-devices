import pydantic.v1.dataclasses
from pydantic import Field
from pydantic.v1 import validator
from tickit.adapters.io import TcpIo
from tickit.core.adapter import AdapterContainer
from tickit.core.components.component import ComponentConfig
from tickit.core.components.system_component import SystemComponent
from tickit.core.typedefs import ComponentID, ComponentPort, PortID

from tickit_devices.zebra._common import param_types
from tickit_devices.zebra.and_or_block import AndOrBlockConfig
from tickit_devices.zebra.zebra import ZebraAdapter


def _default() -> dict[str, int]:
    return dict.fromkeys(param_types.keys(), 0)


@pydantic.v1.dataclasses.dataclass
class Zebra(ComponentConfig):
    """
    Simulation of a Zebra device with a TCP server for reading/setting params/muxes
    (see `ZebraAdapter` for what read/set is available); Block wiring is currently
    invariant while Tickit is running, and only those blocks that are configured in
    components are instantiated.

    Configuration that is currently passed down to Block behaviour from `params`:
    - For AND/OR gates N=1,2,3,4, the following (default 0) may be set
    to Σ2**M where M is each input (1,2,3,4) for which the behaviour is desired.
    {AND|OR}{N}_INV: Inverts input(s) M
    {AND|OR}{N}_ENA: Enables input(s) M
    """

    name: ComponentID
    inputs: dict[PortID, ComponentPort]
    expose: dict[PortID, ComponentPort]
    components: list[AndOrBlockConfig]
    host: str = "localhost"
    port: int = 7012
    params: dict[str, int] = Field(default_factory=dict)

    @validator("params")
    def add_defaults(cls, v: dict[str, int]) -> dict[str, int]:  # noqa: N805
        return {**_default(), **v}

    def __call__(self) -> SystemComponent:
        return SystemComponent(
            adapter=AdapterContainer(
                adapter=ZebraAdapter(params=self.params),
                io=TcpIo(host=self.host, port=self.port),
            ),
            components=self.components,
            expose=self.expose,
            name=self.name,
        )
