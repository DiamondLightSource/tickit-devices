import random
import subprocess
from dataclasses import dataclass

import numpy as np
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

_MXSC_WAVEFORM_WIDTH = 1024


class OAVDevice(Device):
    #: An empty typed mapping of device inputs
    Inputs: TypedDict = TypedDict("Inputs", {})
    #: A typed mapping containing the current output value
    Outputs: TypedDict = TypedDict("Outputs", {})

    def __init__(self):
        pass

    def update(
        self, time: SimTime, inputs: Inputs, callback_period=int(1e9)
    ) -> DeviceUpdate[Outputs]:
        """
        The device is only altered by adapters so take no inputs.

        Args:
            time (SimTime): The current simulation time (in nanoseconds).
            inputs (State): A mapping of inputs to the device and their values.

        Returns:
            DeviceUpdate[Outputs]:
                The produced update event.
        """
        return DeviceUpdate(OAVDevice.Outputs(), SimTime(time + callback_period))


class OAVDeviceMXSC(Device):
    """Class for simulating the PVs in OAV relevant to edge detection.

    We won't try and implement any fancy logic (yet). Just get the PVs hosted.
    """

    #: An empty typed mapping of device inputs
    Inputs: TypedDict = TypedDict("Inputs", {})
    #: A typed mapping containing the current output value
    Outputs: TypedDict = TypedDict("Outputs", {})

    def __init__(self, callback_period=1e9):
        # the pin can be inserted at whatever orientation
        self.callback_period = SimTime(callback_period)
        widest_point = random.uniform(0, 180)
        self.widest_points = (widest_point, widest_point - 180)

        # We arbitrarily decide the widest polynomial should be
        # f(x) = -\frac{1}{360}(x - 180)^2 + 90
        self.widest_point_polynomial = -1 / 360 * (np.arange(0, 340) - 180) ** 2 + 90

        self.omega = random.uniform(-180, 180)

        # For smargons, the limits are set to 0 since it can rotate indefinitely
        self.high_limit_travel = 0
        self.low_limit_travel = 0

        self.tip_x = int(random.uniform(200, 400))
        self.tip_y = int(random.uniform(250, 450))
        self.top = np.zeros(1024)
        ln = np.log(np.arange(1, _MXSC_WAVEFORM_WIDTH + 1 - self.tip_x))
        self.top[self.tip_x : _MXSC_WAVEFORM_WIDTH] = ln
        self.bottom = -self.top
        self.top[self.tip_x :] += self.tip_y
        self.bottom[self.tip_x :] += self.tip_y

        self.set_waveform_based_on_omega()

    def update(self, time: SimTime, inputs: Inputs) -> DeviceUpdate[Outputs]:
        """Update method, will be unused since camera PVs won't change value without \
            directly setting them.

        The device is only altered by adapters so take no inputs.

        Args:
            time (SimTime): The current simulation time (in nanoseconds).
            inputs (State): A mapping of inputs to the device and their values.

        Returns:
            DeviceUpdate[Outputs]:
                The produced update event.
        """
        self.omega = int(
            subprocess.check_output("caget BL03S-MO-SGON-01:OMEGA", shell=True)
        )
        self.set_waveform_based_on_omega()
        return DeviceUpdate(OAVDevice.Outputs(), SimTime(time + self.callback_period))

    def get_omega(self):
        """Getter for pv."""
        return self.omega

    def get_high_limit_travel(self):
        """Getter for pv."""
        return self.high_limit_travel

    def get_low_limit_travel(self):
        """Getter for pv."""
        return self.high_limit_travel

    def get_top(self) -> np.ndarray:
        """Getter for pv."""
        return self.top

    def get_bottom(self) -> np.ndarray:
        """Getter for pv."""
        return self.bottom

    def get_tip_x(self) -> int:
        """Getter for pv."""
        return self.tip_x

    def get_tip_y(self) -> int:
        """Getter for pv."""
        return self.tip_y

    def set_waveform_based_on_omega(self):
        """The pin head is wider if omega is closest to a widest angle."""

        # Get how close omega is to a widest angle.
        # We need to modulo since self.omega could exceed 180
        distance_to_widest = min(
            abs(self.omega - self.widest_points[0]) % 180,
            abs(self.omega - self.widest_points[1]) % 180,
        )
        bulge = self.widest_point_polynomial * (95 - distance_to_widest) / 90
        self.top[self.tip_x : self.tip_x + 340] = bulge + self.tip_y
        self.bottom[self.tip_x : self.tip_x + 340] = -bulge + self.tip_y


class OAVTCPAdapter(ComposedAdapter):
    """A TCP adapter to set a OAVDevice_DIOAV PV values."""

    device: OAVDevice

    def __init__(
        self,
        server: Server,
    ) -> None:
        """OAV adapter, instantiates TcpServer with configured host and port.

        Args:
            server (Server): The immutable data container used to configure a
                server.
        """
        super().__init__(
            server,
            CommandInterpreter(),
        )


class OAVTCPAdapterMXSC(ComposedAdapter):
    device: OAVDeviceMXSC

    def __init__(
        self,
        server: Server,
    ) -> None:
        """OAV adapter, instantiates TcpServer with configured host and port.

        Args:
            server (Server): The immutable data container used to configure a
                server.
        """
        super().__init__(
            server,
            CommandInterpreter(),
        )

    @RegexCommand(r"TOP=(\d+\.?\d*)", interrupt=True, format="utf-8")
    async def set_top(self, value: np.ndarray) -> None:
        """Regex string command that sets the value of beam_current.

        Args:
            value (int): The new value of beam_current.
        """
        self.device.top = value

    @RegexCommand(r"TOP\?", format="utf-8")
    async def get_top(self) -> bytes:
        """Regex string command that returns the utf-8 encoded value of beam_current.

        Returns:
            bytes: The utf-8 encoded value of beam_current.
        """
        return str(self.device.top).encode("utf-8")

    @RegexCommand(r"BOTTOM=(\d+\.?\d*)", interrupt=True, format="utf-8")
    async def set_bottom(self, value: np.ndarray) -> None:
        """Regex string command that sets the value of beam_current.

        Args:
            value (int): The new value of beam_current.
        """
        self.device.bottom = value

    @RegexCommand(r"BOTTOM\?", format="utf-8")
    async def get_bottom(self) -> bytes:
        """Regex string command that returns the utf-8 encoded value of beam_current.

        Returns:
            bytes: The utf-8 encoded value of beam_current.
        """
        return str(self.device.bottom).encode("utf-8")

    @RegexCommand(r"TIPX=(\d+\.?\d*)", interrupt=True, format="utf-8")
    async def set_tip_x(self, value: float) -> None:
        """Regex string command that sets the value of beam_current.

        Args:
            value (int): The new value of beam_current.
        """
        self.device.tip_x = value

    @RegexCommand(r"TIPX\?", format="utf-8")
    async def get_tip_x(self) -> bytes:
        """Regex string command that returns the utf-8 encoded value of beam_current.

        Returns:
            bytes: The utf-8 encoded value of beam_current.
        """
        return str(self.device.tip_x).encode("utf-8")

    @RegexCommand(r"TIPY=(\d+\.?\d*)", interrupt=True, format="utf-8")
    async def set_tip_y(self, value: float) -> None:
        """Regex string command that sets the value of beam_current.

        Args:
            value (int): The new value of beam_current.
        """
        self.device.tip_y = value

    @RegexCommand(r"TIPY\?", format="utf-8")
    async def get_tip_y(self) -> bytes:
        """Regex string command that returns the utf-8 encoded value of beam_current.

        Returns:
            bytes: The utf-8 encoded value of beam_current.
        """
        return str(self.device.tip_y).encode("utf-8")


class OAVEpicsAdapterMXSC(EpicsAdapter):
    """
    Epics adapter for handling edge detection PVs.
    """

    device: OAVDeviceMXSC

    # Put all the PVs on EPICS
    def on_db_load(self) -> None:
        """Epics adapter for reading device values as a PV through channel access."""
        self.link_input_on_interrupt(
            builder.WaveformOut("MXSC:Top", self.device.top), self.device.get_top
        )
        self.link_input_on_interrupt(
            builder.WaveformOut("MXSC:Bottom", self.device.bottom),
            self.device.get_bottom,
        )
        self.link_input_on_interrupt(builder.aOut("MXSC:TipX"), self.device.get_tip_x)
        self.link_input_on_interrupt(builder.aOut("MXSC:TipY"), self.device.get_tip_y)


class OAVEpicsAdapter(EpicsAdapter):
    """Epics adapter for reading all Attributes as a PV through channel access."""

    device: OAVDevice

    # Put all the PVs on EPICS
    def on_db_load(self) -> None:
        """Epics adapter for reading device values as a PV through channel access."""
        pass


@dataclass
class OAV_DEVICE_DEFAULT(ComponentConfig):
    """Parent class for various OAV devices."""

    name: str
    db_file: str
    port: int
    ioc_name: str
    host: str = "localhost"
    format: ByteFormat = ByteFormat(b"%b\r\n")

    def __call__(self) -> Component:
        """Set up simulation."""
        return DeviceSimulation(
            name=self.name,
            device=OAVDevice(),
            adapters=[
                OAVTCPAdapter(TcpServer(self.host, self.port, self.format)),
                OAVEpicsAdapter(self.db_file, self.ioc_name),
            ],
        )


@dataclass
class OAV_DI_OAV(ComponentConfig):
    """To hold DI-OAV PVs."""

    name: str
    db_file: str
    port: int
    ioc_name: str
    host: str = "localhost"
    format: ByteFormat = ByteFormat(b"%b\r\n")

    def __call__(self) -> Component:
        """Set up simulation."""
        return DeviceSimulation(
            name=self.name,
            device=OAVDeviceMXSC(),
            adapters=[
                OAVTCPAdapterMXSC(
                    TcpServer(
                        self.host,
                        self.port,
                        self.format,
                    )
                ),
                OAVEpicsAdapterMXSC(self.db_file, self.ioc_name),
            ],
        )
