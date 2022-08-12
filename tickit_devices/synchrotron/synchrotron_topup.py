from dataclasses import dataclass

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


class SynchrotronTopUpDevice(Device):
    """Device to simulate the top up records from the synchrotron.

    The signal is read via an epics adapter, and set using a tcp adapter.
    """

    #: An empty typed mapping of device inputs
    Inputs: TypedDict = TypedDict("Inputs", {})
    #: A typed mapping containing the current output value
    Outputs: TypedDict = TypedDict(
        "Outputs",
        {
            "countdown": float,
            "end_countdown": float,
        },
    )

    def __init__(
        self,
        initial_countdown: float,
        initial_end_countdown: float,
    ) -> None:
        """Initialise the SynchrotonTopUp device.

        Args:
            initial_countdown (float): Initial countdown value
            initial_end_countdown (float): Initial end countdown value
        """
        self.countdown = initial_countdown
        self.end_countdown = initial_end_countdown

    def update(self, time: SimTime, inputs: Inputs) -> DeviceUpdate[Outputs]:
        """Update method that outputs top up record values.

        The device is only altered by adapters so take no inputs.

        Args:
            time (SimTime): The current simulation time (in nanoseconds).
            inputs (State): A mapping of inputs to the device and their values.

        Returns:
            DeviceUpdate[Outputs]:
                The produced update event which contains the value of the machine
                top up records.
        """
        return DeviceUpdate(
            SynchrotronTopUpDevice.Outputs(
                countdown=self.countdown,
                end_countdown=self.end_countdown,
            ),
            None,
        )

    def get_countdown(self) -> float:
        """Return value of countdown, required for epics adapter."""
        return self.countdown

    def get_end_countdown(self) -> float:
        """Return value of end_countdown, required for epics adapter."""
        return self.end_countdown


class SynchrotronTopUpTCPAdapter(ComposedAdapter):
    """A TCP adapter to set a SynchrotronTopUpDevice PV values."""

    device: SynchrotronTopUpDevice

    def __init__(
        self,
        server: Server,
    ) -> None:
        """Synchrotron adapter, instantiates TcpServer with configured host and port.

        Args:
            server (Server): The immutable data container used to configure a
                server.
        """
        super().__init__(
            server,
            CommandInterpreter(),
        )

    @RegexCommand(r"CD=(\d+\.?\d*)", interrupt=True, format="utf-8")
    async def set_countdown(self, value: float) -> None:
        """Regex string command to set the value of countdown.

        Args:
            value (int): The new value of countdown.
        """
        self.device.countdown = value

    @RegexCommand(r"ECD=(\d+\.?\d*)", interrupt=True, format="utf-8")
    async def set_end_countdown(self, value: float) -> None:
        """Regex string command to set the value of end_countdown.

        Args:
            value (int): The new value of end_countdown.
        """
        self.device.end_countdown = value

    @RegexCommand(r"CD\?", format="utf-8")
    async def get_countdown(self) -> bytes:
        """Regex string command that returns countdown.

        Returns:
            bytes: The utf-8 encoded value of countdown.
        """
        return str(self.device.countdown).encode("utf-8")

    @RegexCommand(r"ECD\?", format="utf-8")
    async def get_end_countdown(self) -> bytes:
        """Regex string command that returns end_countdown.

        Returns:
            bytes: The utf-8 encoded value of end_countdown.
        """
        return str(self.device.end_countdown).encode("utf-8")


class SynchrotronTopUpEpicsAdapter(EpicsAdapter):
    """Epics adapter for reading device values as a PV through channel access."""

    device: SynchrotronTopUpDevice

    def on_db_load(self) -> None:
        """Link epics records with getters for device."""
        self.link_input_on_interrupt(
            builder.aIn("COUNTDOWN"), self.device.get_countdown
        )
        self.link_input_on_interrupt(
            builder.aIn("ENDCOUNTDN"),
            self.device.get_end_countdown,
        )


@dataclass
class SynchrotronTopUp(ComponentConfig):
    """Synchrotron top up status component."""

    initial_countdown: float = 600
    initial_end_countdown: float = 610
    host: str = "localhost"
    port: int = 25565
    format: ByteFormat = ByteFormat(b"%b\r\n")
    db_file: str = "tickit_devices/synchrotron/db_files/FILL.db"
    ioc_name: str = "BL03S-SR-CS-FILL-01"

    def __call__(self) -> Component:  # noqa: D102
        return DeviceSimulation(
            name=self.name,
            device=SynchrotronTopUpDevice(
                self.initial_countdown,
                self.initial_end_countdown,
            ),
            adapters=[
                SynchrotronTopUpTCPAdapter(
                    TcpServer(self.host, self.port, self.format)
                ),
                SynchrotronTopUpEpicsAdapter(self.db_file, self.ioc_name),
            ],
        )
