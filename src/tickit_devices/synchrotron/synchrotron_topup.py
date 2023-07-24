import pathlib
from dataclasses import dataclass
from typing import TypedDict

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


class SynchrotronTopUpDevice(Device):
    """Device to simulate the top up records from the synchrotron.

    The signal is read via an epics adapter, and set using a tcp adapter.
    """

    #: An empty typed mapping of device inputs
    Inputs: TypedDict = TypedDict("Inputs", {"current": float})
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
        initial_countdown: float = 600.0,
        initial_end_countdown: float = 620.0,
        callback_period: int = int(1e9),
        last_current: float = 300.0,
        target_current: float = 300.0,
        minimum_current: float = 270.0,
    ) -> None:
        """Initialise the SynchrotonTopUp device.

        Args:
            initial_countdown (float): Length of time in seconds to deplete
                charge from target_current to minimum_current.
            initial_end_countdown (float): Length of time in seconds to topup the charge
                from minimum_current to target_current.
            callback_period (int): number of nanoseconds to wait before calling again
            last_current (float): Can be set in case the user doesn't want to assume
                the simulation starts at a current of 300mA.
            target_current: The current the device will be topped up to.
            minimum_current (float): The current the synchrotron can fall
                to before topup.
        """
        # Countdown is typically 10 minutes
        self.countdown = self.initial_countdown = initial_countdown

        self.default_fill_time = initial_end_countdown - initial_countdown
        self.target_current = target_current
        self.minimum_current = minimum_current

        # End countdown is typically 10 minutes of countdown, then 10 seconds of fill
        self.end_countdown = self.initial_end_countdown = initial_end_countdown
        self.fill_time = initial_end_countdown - initial_countdown

        self.callback_period = callback_period

        self.last_current = last_current
        self.last_time = None
        self.topup_fill = False

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
        new_current = inputs["current"]

        current_difference = new_current - self.last_current

        topup_fill = current_difference > 0

        # calculate the number of updates to go until topup stage begins or
        # ends: based upon the change of the current.
        updates_to_go = abs(
            topup_fill * (self.target_current - new_current) / current_difference
            + (not topup_fill)
            * (new_current - self.minimum_current)
            / current_difference
        )

        period = self.callback_period * 1e-9
        if self.last_time:
            period = (time - self.last_time) * 1e-9

        self.countdown = (not topup_fill) * (updates_to_go * period)

        # assume topup fill will take 15 seconds, and calculate it directly during
        self.fill_time = topup_fill * (updates_to_go * period) + (
            not topup_fill * self.default_fill_time
        )
        self.end_countdown = self.countdown + self.fill_time

        self.last_current = new_current
        self.last_time = time
        call_at = SimTime(time + self.callback_period)
        return DeviceUpdate(
            SynchrotronTopUpDevice.Outputs(
                countdown=self.countdown,
                end_countdown=self.end_countdown,
            ),
            call_at,
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
    initial_end_countdown: float = 620
    callback_period: int = int(1e9)
    host: str = "localhost"
    port: int = 25565
    format: ByteFormat = ByteFormat(b"%b\r\n")
    db_file: str = str(pathlib.Path(__file__).parent.absolute() / "db_files/FILL.db")
    ioc_name: str = "SR-CS-FILL-01"

    def __call__(self) -> Component:  # noqa: D102
        return DeviceSimulation(
            name=self.name,
            device=SynchrotronTopUpDevice(
                self.initial_countdown,
                self.initial_end_countdown,
                callback_period=self.callback_period,
            ),
            adapters=[
                SynchrotronTopUpTCPAdapter(
                    TcpServer(self.host, self.port, self.format)
                ),
                SynchrotronTopUpEpicsAdapter(self.ioc_name, self.db_file),
            ],
        )
