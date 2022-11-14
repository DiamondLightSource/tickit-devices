from dataclasses import dataclass

import numpy as np
from tickit.adapters.composed import ComposedAdapter
from tickit.adapters.epicsadapter import EpicsAdapter
from tickit.adapters.interpreters.command import CommandInterpreter
from tickit.adapters.servers.tcp import TcpServer
from tickit.core.adapter import Server
from tickit.core.components.component import Component, ComponentConfig
from tickit.core.components.device_simulation import DeviceSimulation
from tickit.core.device import Device, DeviceUpdate
from tickit.core.typedefs import SimTime
from tickit.utils.byte_format import ByteFormat
from tickit.utils.compat.typing_compat import TypedDict


class OAVDevice(Device):
    """Class for simulating the PVs in OAV relevant to edge detection.

    We won't try and implement any fancy logic (yet). Just get the PVs hosted.
    """

    #: An empty typed mapping of device inputs
    Inputs: TypedDict = TypedDict("Inputs", {})
    #: A typed mapping containing the current output value
    Outputs: TypedDict = TypedDict("Outputs", {})

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
        return DeviceUpdate(OAVDevice.Outputs(), None)


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


class OAVEpicsAdapter(EpicsAdapter):
    """Epics Adapter.

    Epics adapter for reading all Attributes as a PV
    through channel access.
    """

    device: OAVDevice

    # Put all the PVs on EPICS
    def on_db_load(self) -> None:
        """Epics adapter for reading device values as a PV through channel access."""
        pass


@dataclass
class OAV_DI_OAV(ComponentConfig):
    """To hold DI-OAV PVs."""

    waveforms_file: str = "tickit_devices/oav/db_files/edge_waveforms.npy"
    host: str = "localhost"
    port: int = 25565
    format: ByteFormat = ByteFormat(b"%b\r\n")
    db_file: str = "tickit_devices/oav/db_files/DI-OAV.db"
    ioc_name: str = "S03SIM-DI-OAV-01"

    def __call__(self) -> Component:  # noqa: D102
        with open(self.waveforms_file, "rb") as f:
            self.initial_edgeTop = np.load(f)
            self.initial_edgeBottom = np.load(f)
        return DeviceSimulation(
            name=self.name,
            device=OAVDevice(),
            adapters=[
                OAVTCPAdapter(TcpServer(self.host, self.port, self.format)),
                OAVEpicsAdapter(self.db_file, self.ioc_name),
            ],
        )


@dataclass
class OAV_DI_IOC(ComponentConfig):
    """To hold DI-IOC PVs."""

    waveforms_file: str = "tickit_devices/oav/db_files/edge_waveforms.npy"
    host: str = "localhost"
    port: int = 25565
    format: ByteFormat = ByteFormat(b"%b\r\n")
    db_file: str = "tickit_devices/oav/db_files/DI-IOC.db"
    ioc_name: str = "S03SIM-DI-IOC-01"

    def __call__(self) -> Component:  # noqa: D102
        with open(self.waveforms_file, "rb") as f:
            self.initial_edgeTop = np.load(f)
            self.initial_edgeBottom = np.load(f)
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

    waveforms_file: str = "tickit_devices/oav/db_files/edge_waveforms.npy"
    host: str = "localhost"
    port: int = 25565
    format: ByteFormat = ByteFormat(b"%b\r\n")
    db_file: str = "tickit_devices/oav/db_files/EA-FSCN.db"
    ioc_name: str = "S03SIM-EA-FSCN-01"

    def __call__(self) -> Component:  # noqa: D102
        with open(self.waveforms_file, "rb") as f:
            self.initial_edgeTop = np.load(f)
            self.initial_edgeBottom = np.load(f)
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

    waveforms_file: str = "tickit_devices/oav/db_files/edge_waveforms.npy"
    host: str = "localhost"
    port: int = 25565
    format: ByteFormat = ByteFormat(b"%b\r\n")
    db_file: str = "tickit_devices/oav/db_files/EA-OAV.db"
    ioc_name: str = "S03SIM-EA-OAV-01"

    def __call__(self) -> Component:  # noqa: D102
        with open(self.waveforms_file, "rb") as f:
            self.initial_edgeTop = np.load(f)
            self.initial_edgeBottom = np.load(f)
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
    """To hold EA-OAV PVs."""

    waveforms_file: str = "tickit_devices/oav/db_files/edge_waveforms.npy"
    host: str = "localhost"
    port: int = 25565
    format: ByteFormat = ByteFormat(b"%b\r\n")
    db_file: str = "tickit_devices/oav/db_files/EA-BL.db"
    ioc_name: str = "S03SIM-EA-BL-01"

    def __call__(self) -> Component:  # noqa: D102
        with open(self.waveforms_file, "rb") as f:
            self.initial_edgeTop = np.load(f)
            self.initial_edgeBottom = np.load(f)
        return DeviceSimulation(
            name=self.name,
            device=OAVDevice(),
            adapters=[
                OAVTCPAdapter(TcpServer(self.host, self.port, self.format)),
                OAVEpicsAdapter(self.db_file, self.ioc_name),
            ],
        )
