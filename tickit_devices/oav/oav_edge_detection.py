import random
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

        # we arbitrarily decide the widest polynomial should be
        # f(x) = -\frac{1}{360}(x - 180)^2 + 90
        self.widest_point_polynomial = -1 / 360 * (np.arange(0, 340) - 180) ** 2 + 90

        self.omega = random.uniform(-180, 180)

        # For smargons, the limits are set to 0 since it can rotate indefinitely
        self.high_limit_travel = 0
        self.low_limit_travel = 0

        self.tip_x = int(random.uniform(10, 250))
        self.tip_y = int(random.uniform(300, 500))
        self.top = np.zeros(1024)
        ln = np.log(np.arange(1, 1025 - self.tip_x))
        self.top[self.tip_x : 1024] = ln
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
        distance_to_widest = 0
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

    @RegexCommand(r"C=(\d+\.?\d*)", interrupt=True, format="utf-8")
    async def set_top(self, value: np.ndarray) -> None:
        """Regex string command that sets the value of beam_current.

        Args:
            value (int): The new value of beam_current.
        """
        self.device.top = value

    @RegexCommand(r"C\?", format="utf-8")
    async def get_top(self) -> bytes:
        """Regex string command that returns the utf-8 encoded value of beam_current.

        Returns:
            bytes: The utf-8 encoded value of beam_current.
        """
        return str(self.device.top).encode("utf-8")

    @RegexCommand(r"C=(\d+\.?\d*)", interrupt=True, format="utf-8")
    async def set_bottom(self, value: np.ndarray) -> None:
        """Regex string command that sets the value of beam_current.

        Args:
            value (int): The new value of beam_current.
        """
        self.device.bottom = value

    @RegexCommand(r"C\?", format="utf-8")
    async def get_bottom(self) -> bytes:
        """Regex string command that returns the utf-8 encoded value of beam_current.

        Returns:
            bytes: The utf-8 encoded value of beam_current.
        """
        return str(self.device.bottom).encode("utf-8")

    @RegexCommand(r"C=(\d+\.?\d*)", interrupt=True, format="utf-8")
    async def set_tip_x(self, value: float) -> None:
        """Regex string command that sets the value of beam_current.

        Args:
            value (int): The new value of beam_current.
        """
        self.device.tip_x = value

    @RegexCommand(r"C\?", format="utf-8")
    async def get_tip_x(self) -> bytes:
        """Regex string command that returns the utf-8 encoded value of beam_current.

        Returns:
            bytes: The utf-8 encoded value of beam_current.
        """
        return str(self.device.tip_x).encode("utf-8")

    @RegexCommand(r"C=(\d+\.?\d*)", interrupt=True, format="utf-8")
    async def set_tip_y(self, value: float) -> None:
        """Regex string command that sets the value of beam_current.

        Args:
            value (int): The new value of beam_current.
        """
        self.device.tip_y = value

    @RegexCommand(r"C\?", format="utf-8")
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
    """
    Epics adapter for reading all Attributes as a PV through channel access.
    """

    device: OAVDevice

    # Put all the PVs on EPICS
    def on_db_load(self) -> None:
        """Epics adapter for reading device values as a PV through channel access."""
        pass


@dataclass
class OAV_DI_OAV(ComponentConfig):
    """To hold DI-OAV PVs."""

    host: str = "localhost"
    port: int = 25565
    format: ByteFormat = ByteFormat(b"%b\r\n")
    db_file: str = "tickit_devices/oav/db_files/DI-OAV.db"
    ioc_name: str = "BL03S-DI-OAV-01"

    def __call__(self) -> Component:  # noqa: D102
        return DeviceSimulation(
            name=self.name,
            device=OAVDeviceMXSC(),
            adapters=[
                OAVTCPAdapterMXSC(TcpServer(self.host, self.port, self.format)),
                OAVEpicsAdapterMXSC(self.db_file, self.ioc_name),
            ],
        )


@dataclass
class OAV_DI_IOC(ComponentConfig):
    """To hold DI-IOC PVs."""

    host: str = "localhost"
    port: int = 25564
    format: ByteFormat = ByteFormat(b"%b\r\n")
    db_file: str = "tickit_devices/oav/db_files/DI-IOC.db"
    ioc_name: str = "BL03S-DI-IOC-01"

    def __call__(self) -> Component:  # noqa: D102
        return DeviceSimulation(
            name=self.name,
            device=OAVDevice(),
            adapters=[
                OAVTCPAdapter(TcpServer(self.host, self.port, self.format)),
                OAVEpicsAdapter(self.db_file, self.ioc_name),
            ],
        )


@dataclass
class OAV_EA_FSCN(ComponentConfig):
    """To hold EA-FSCN PVs."""

    host: str = "localhost"
    port: int = 25563
    format: ByteFormat = ByteFormat(b"%b\r\n")
    db_file: str = "tickit_devices/oav/db_files/EA-FSCN.db"
    ioc_name: str = "BL03S-EA-FSCN-01"

    def __call__(self) -> Component:  # noqa: D102
        return DeviceSimulation(
            name=self.name,
            device=OAVDevice(),
            adapters=[
                OAVTCPAdapter(TcpServer(self.host, self.port, self.format)),
                OAVEpicsAdapter(self.db_file, self.ioc_name),
            ],
        )


@dataclass
class OAV_EA_OAV(ComponentConfig):
    """To hold EA-OAV PVs."""

    host: str = "localhost"
    port: int = 25562
    format: ByteFormat = ByteFormat(b"%b\r\n")
    db_file: str = "tickit_devices/oav/db_files/EA-OAV.db"
    ioc_name: str = "BL03S-EA-OAV-01"

    def __call__(self) -> Component:  # noqa: D102
        return DeviceSimulation(
            name=self.name,
            device=OAVDevice(),
            adapters=[
                OAVTCPAdapter(TcpServer(self.host, self.port, self.format)),
                OAVEpicsAdapter(self.db_file, self.ioc_name),
            ],
        )


@dataclass
class OAV_EA_BL(ComponentConfig):
    """To hold EA-BL PVs."""

    host: str = "localhost"
    port: int = 25561
    format: ByteFormat = ByteFormat(b"%b\r\n")
    db_file: str = "tickit_devices/oav/db_files/EA-BL.db"
    ioc_name: str = "BL03S-EA-BL-01"

    def __call__(self) -> Component:  # noqa: D102
        return DeviceSimulation(
            name=self.name,
            device=OAVDevice(),
            adapters=[
                OAVTCPAdapter(TcpServer(self.host, self.port, self.format)),
                OAVEpicsAdapter(self.db_file, self.ioc_name),
            ],
        )


@dataclass
class OAV_MO_IOC(ComponentConfig):
    """To hold MO-IOC PVs."""

    host: str = "localhost"
    port: int = 25560
    format: ByteFormat = ByteFormat(b"%b\r\n")
    db_file: str = "tickit_devices/oav/db_files/MO-IOC.db"
    ioc_name: str = "BL03S-MO-IOC-01"

    def __call__(self) -> Component:  # noqa: D102
        return DeviceSimulation(
            name=self.name,
            device=OAVDevice(),
            adapters=[
                OAVTCPAdapter(TcpServer(self.host, self.port, self.format)),
                OAVEpicsAdapter(self.db_file, self.ioc_name),
            ],
        )
