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


class SynchrotronMachineStatusDevice(Device):
    """Device to simulate the machine status records from the synchrotron.

    The signal is read via and epics adapter, and set using a tcp adapter.
    """

    #: An empty typed mapping of device inputs
    Inputs: TypedDict = TypedDict("Inputs", {})
    #: A typed mapping containing the current output value
    Outputs: TypedDict = TypedDict(
        "Outputs",
        {
            "mode": int,
            "user_countdown": float,
            "beam_energy": float,
        },
    )

    def __init__(
        self,
        initial_mode: int,
        initial_countdown: float,
        initial_energy: float,
    ) -> None:
        """Initialise the SynchrotonMachineStatus device.

        Args:
            synchrotron_mode (str): The synchrotron operation status
            user_countdown (float): Time countdown to the beam dump
            beam_energy (float): Current value of ring energy
        """
        self.synchrotron_mode = initial_mode
        self.user_countdown = initial_countdown
        self.beam_energy = initial_energy

    def update(self, time: SimTime, inputs: Inputs) -> DeviceUpdate[Outputs]:
        """Update method that outputs machine status record values.

        The device is only altered by adapters so take no inputs and is independent of
        time.

        Args:
            time (SimTime): The current simulation time (in nanoseconds).
            inputs (State): A mapping of inputs to the device and their values.

        Returns:
            DeviceUpdate[Outputs]:
                The produced update event which contains the value of the machine
                status records.
        """
        return DeviceUpdate(
            SynchrotronMachineStatusDevice.Outputs(
                mode=self.synchrotron_mode,
                user_countdown=self.user_countdown,
                beam_energy=self.beam_energy,
            ),
            None,
        )

    def get_mode(self) -> int:
        return self.synchrotron_mode

    def get_user_countdown(self) -> float:
        return self.user_countdown

    def get_beam_energy(self) -> float:
        return self.beam_energy


class SynchrotronMachineStatusTCPAdapter(ComposedAdapter):
    """A TCP adapter to set a SynchrotronMachineStatusDevice PV values."""

    device: SynchrotronMachineStatusDevice

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

    @RegexCommand(r"mode=([0-7])", interrupt=True, format="utf-8")
    async def set_synchrotron_mode(self, value: int) -> None:
        """Regex string command to set the value of synchrotron_mode."""
        self.device.synchrotron_mode = value

    @RegexCommand(r"BDC=(\d+\.?\d*)", interrupt=True, format="utf-8")
    async def set_user_countdown(self, value: float) -> None:
        """Regex string command to set the value of user_countdown."""
        self.device.user_countdown = value

    @RegexCommand(r"RE=(\d+\.?\d*)", interrupt=True, format="utf-8")
    async def set_beam_energy(self, value: float) -> None:
        """Regex string command to set the value of beam_energy."""
        self.device.beam_energy = value

    @RegexCommand(r"mode\?", format="utf-8")
    async def get_synchrotron_mode(self) -> bytes:
        """Regex string command that returns synchrotron_mode."""
        return str(self.device.synchrotron_mode).encode("utf-8")

    @RegexCommand(r"BDC\?", format="utf-8")
    async def get_user_countdown(self) -> bytes:
        """Regex string command that returns user_countdown."""
        return str(self.device.user_countdown).encode("utf-8")

    @RegexCommand(r"RE\?", format="utf-8")
    async def get_beam_energy(self) -> bytes:
        """Regex string command that returns beam_energy."""
        return str(self.device.beam_energy).encode("utf-8")


class SynchrotronMachineStatusEpicsAdapter(EpicsAdapter):
    """Epics adapter for reading device values as a PV through channel access."""

    device: SynchrotronMachineStatusDevice

    def on_db_load(self) -> None:
        """Link loaded in record with getter for device."""
        self.link_input_on_interrupt(builder.mbbIn("MODE"), self.device.get_mode)
        self.link_input_on_interrupt(
            builder.aIn("USERCOUNTDOWN"), self.device.get_user_countdown
        )
        self.link_input_on_interrupt(
            builder.aIn("BEAMENERGY"), self.device.get_beam_energy
        )
        # self.link_input_on_interrupt(
        #     builder.calcout("USERCOUNTDOWN"), self.device.get_user_countdown
        # )
        # self.link_input_on_interrupt(
        #     builder.calc("BEAMENERGY"), self.device.get_beam_energy
        # )


@dataclass
class SynchrotronMachineStatus(ComponentConfig):
    """Synchrotron Machine status component."""

    initial_mode: int = 0
    initial_countdown: float = 1.0
    initial_energy: float = 2.0
    host: str = "localhost"
    port: int = 25565
    format: ByteFormat = ByteFormat(b"%b\r\n")
    db_file: str = "artemis/synchrotron/db_files/MSTAT.db"
    ioc_name: str = "SYNCHROTRON-MACHINE"

    def __call__(self) -> Component:  # noqa: D102
        return DeviceSimulation(
            name=self.name,
            device=SynchrotronMachineStatusDevice(
                self.initial_mode,
                self.initial_countdown,
                self.initial_energy,
            ),
            adapters=[
                SynchrotronMachineStatusTCPAdapter(
                    TcpServer(self.host, self.port, self.format)
                ),
                SynchrotronMachineStatusEpicsAdapter(self.db_file, self.ioc_name),
            ],
        )
