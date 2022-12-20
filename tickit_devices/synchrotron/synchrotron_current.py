from dataclasses import dataclass
from typing import Optional

from softioc import builder
from tickit.adapters.composed import ComposedAdapter
from tickit.adapters.epicsadapter import EpicsAdapter
from tickit.adapters.interpreters.command import CommandInterpreter, RegexCommand
from tickit.adapters.servers.tcp import TcpServer
from tickit.core.adapter import Server
from tickit.core.components.component import Component, ComponentConfig
from tickit.core.components.device_simulation import DeviceSimulation
from tickit.core.device import Device, DeviceUpdate
from tickit.core.typedefs import SimTime
from tickit.utils.byte_format import ByteFormat
from tickit.utils.compat.typing_compat import TypedDict


class SynchrotronCurrentDevice(Device):
    """Device to simulate the ring current signal value from the synchrotron.

    This SynchrotronCurrentDevice simulates only a single signal that can be read,
    the beam current.The real world pv for this current is SR-DI-DCCT-01:SIGNAL.

    The signal is read via and epics adapter, and set using a tcp adapter.
    """

    #: An empty typed mapping of device inputs
    Inputs: TypedDict = TypedDict("Inputs", {})
    #: A typed mapping containing the current output value
    Outputs: TypedDict = TypedDict("Outputs", {"current": float})

    def __init__(self, initial_current: Optional[float]) -> None:
        """Initialise the SynchrotonCurrent device.

        Args:
            initial_current (Optional[float]): The inital beam current. Defaults to
                300mA
        """
        self.beam_current = initial_current if initial_current is not None else 300

    def update(self, time: SimTime, inputs: Inputs) -> DeviceUpdate[Outputs]:
        """Update method that just outputs beam current.

        The device is only altered by adapters so take no inputs.

        Args:
            time (SimTime): The current simulation time (in nanoseconds).
            inputs (State): A mapping of inputs to the device and their values.

        Returns:
            DeviceUpdate[Outputs]:
                The produced update event which contains the value of the beam current.
        """
        return DeviceUpdate(
            SynchrotronCurrentDevice.Outputs(current=self.beam_current), None
        )

    def get_current(self) -> float:
        """Beam current getter for the epics adapter."""
        return self.beam_current


class SynchrotronCurrentTCPAdapter(ComposedAdapter):
    """A TCP adapter to set a SynchrotronCurrentDevice PV values."""

    device: SynchrotronCurrentDevice

    def __init__(
        self,
        server: Server,
    ) -> None:
        """
        TCP adapter, instantiates TcpServer with configured host and port.

        Args:
            server (Server): The immutable data container used to configure a
                server.
        """
        super().__init__(
            server,
            CommandInterpreter(),
        )

    @RegexCommand(r"C=(\d+\.?\d*)", interrupt=True, format="utf-8")
    async def set_beam_current(self, value: float) -> None:
        """Regex string command that sets the value of beam_current.

        Args:
            value (int): The new value of beam_current.
        """
        self.device.beam_current = value

    @RegexCommand(r"C\?", format="utf-8")
    async def get_beam_current(self) -> bytes:
        """Regex string command that returns the utf-8 encoded value of beam_current.

        Returns:
            bytes: The utf-8 encoded value of beam_current.
        """
        return str(self.device.beam_current).encode("utf-8")


class SynchrotronCurrentEpicsAdapter(EpicsAdapter):
    """Epics adapter for reading device current as a PV through channel access."""

    device: SynchrotronCurrentDevice

    def on_db_load(self) -> None:
        """Link loaded in record with getter for device."""
        self.link_input_on_interrupt(builder.aIn("SIGNAL"), self.device.get_current)


@dataclass
class SynchrotronCurrent(ComponentConfig):
    """Synchrotron current component."""

    initial_current: Optional[float] = None
    host: str = "localhost"
    port: int = 25565
    format: ByteFormat = ByteFormat(b"%b\r\n")
    db_file: str = "tickit_devices/synchrotron/db_files/DCCT.db"
    ioc_name: str = "BL03S-SR-DI-DCCT-01"

    def __call__(self) -> Component:  # noqa: D102
        return DeviceSimulation(
            name=self.name,
            device=SynchrotronCurrentDevice(self.initial_current),
            adapters=[
                SynchrotronCurrentTCPAdapter(
                    TcpServer(self.host, self.port, self.format)
                ),
                SynchrotronCurrentEpicsAdapter(self.db_file, self.ioc_name),
            ],
        )
