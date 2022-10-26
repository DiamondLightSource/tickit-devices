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


class OAVEdgeDetectionDevice(Device):
    """Class for simulating the PVs in OAV relevant to edge detection.

    We won't try and implement any fancy logic (yet). Just get the PVs hosted.
    """

    #: An empty typed mapping of device inputs
    Inputs: TypedDict = TypedDict("Inputs", {})
    #: A typed mapping containing the current output value
    Outputs: TypedDict = TypedDict("Outputs", {})

    def __init__(
        self,
        initial_exposurePV,
        initial_acqPeriodPV,
        initial_gainPV,
        initial_oavColourMode,
        initial_xSizePV,
        initial_ySizePV,
        initial_inputRBPV,
        initial_exposureRBPV,
        initial_acqPeriodRBPV,
        initial_gainRBPV,
        initial_inputPV,
        initial_enableOverlayPV,
        initial_overlayPortPV,
        initial_useOverlay1PV,
        initial_useOverlay2PV,
        initial_overlay2ShapePV,
        initial_overlay2RedPV,
        initial_overlay2GreenPV,
        initial_overlay2BluePV,
        initial_overlay2XPosition,
        initial_overlay2YPosition,
        initial_overlay2XSize,
        initial_overlay2YSize,
        initial_edgeTop,
        initial_edgeBottom,
    ) -> None:
        """Initialise the OAVEdgeDetectionDevice device."""
        # Edge detection PVs
        self.exposurePV = {
            "pv_name": "CAM:AcquireTime",
            "getter": self.get_exposurePV_value,
            "value": initial_exposurePV,
        }
        self.acqPeriodPV = {
            "pv_name": "CAM:AcquirePeriod",
            "getter": self.get_acqPeriodPV_value,
            "value": initial_acqPeriodPV,
        }
        self.gainPV = {
            "pv_name": "CAM:Gain",
            "getter": self.get_gainPV_value,
            "value": initial_gainPV,
        }
        self.oavColourMode = {
            "pv_name": "CAM:ColorMode",
            "getter": self.get_oavColourMode_value,
            "value": initial_oavColourMode,
        }
        self.xSizePV = {
            "pv_name": "MJPG:ArraySize1_RBV",
            "getter": self.get_xSizePV_value,
            "value": initial_xSizePV,
        }
        self.ySizePV = {
            "pv_name": "MJPG:ArraySize2_RBV",
            "getter": self.get_ySizePV_value,
            "value": initial_ySizePV,
        }
        self.inputRBPV = {
            "pv_name": "MJPG:NDArrayPort_RBV",
            "getter": self.get_inputRBPV_value,
            "value": initial_inputRBPV,
        }
        self.exposureRBPV = {
            "pv_name": "CAM:AcquireTime_RBV",
            "getter": self.get_exposureRBPV_value,
            "value": initial_exposureRBPV,
        }
        self.acqPeriodRBPV = {
            "pv_name": "CAM:AcquirePeriod_RBV",
            "getter": self.get_acqPeriodRBPV_value,
            "value": initial_acqPeriodRBPV,
        }
        self.gainRBPV = {
            "pv_name": "CAM:Gain_RBV",
            "getter": self.get_gainRBPV_value,
            "value": initial_gainRBPV,
        }
        self.inputPV = {
            "pv_name": "MJPG:NDArrayPort",
            "getter": self.get_inputPV_value,
            "value": initial_inputPV,
        }
        self.enableOverlayPV = {
            "pv_name": "OVER:EnableCallbacks",
            "getter": self.get_enableOverlayPV_value,
            "value": initial_enableOverlayPV,
        }
        self.overlayPortPV = {
            "pv_name": "OVER:NDArrayPort",
            "getter": self.get_overlayPortPV_value,
            "value": initial_overlayPortPV,
        }
        self.useOverlay1PV = {
            "pv_name": "OVER:1:Use",
            "getter": self.get_useOverlay1PV_value,
            "value": initial_useOverlay1PV,
        }
        self.useOverlay2PV = {
            "pv_name": "OVER:2:Use",
            "getter": self.get_useOverlay2PV_value,
            "value": initial_useOverlay2PV,
        }
        self.overlay2ShapePV = {
            "pv_name": "OVER:2:Shape",
            "getter": self.get_overlay2ShapePV_value,
            "value": initial_overlay2ShapePV,
        }
        self.overlay2RedPV = {
            "pv_name": "OVER:2:Red",
            "getter": self.get_overlay2RedPV_value,
            "value": initial_overlay2RedPV,
        }
        self.overlay2GreenPV = {
            "pv_name": "OVER:2:Green",
            "getter": self.get_overlay2GreenPV_value,
            "value": initial_overlay2GreenPV,
        }
        self.overlay2BluePV = {
            "pv_name": "OVER:2:Blue",
            "getter": self.get_overlay2BluePV_value,
            "value": initial_overlay2BluePV,
        }
        self.overlay2XPosition = {
            "pv_name": "OVER:2:PositionX",
            "getter": self.get_overlay2XPosition_value,
            "value": initial_overlay2XPosition,
        }
        self.overlay2YPosition = {
            "pv_name": "OVER:2:PositionY",
            "getter": self.get_overlay2YPosition_value,
            "value": initial_overlay2YPosition,
        }
        self.overlay2XSize = {
            "pv_name": "OVER:2:SizeX",
            "getter": self.get_overlay2XSize_value,
            "value": initial_overlay2XSize,
        }
        self.overlay2YSize = {
            "pv_name": "OVER:2:SizeY",
            "getter": self.get_overlay2YSize_value,
            "value": initial_overlay2YSize,
        }
        self.edgeTop = {
            "pv_name": "MXSC:Top",
            "getter": self.get_edgeTop_value,
            "value": initial_edgeTop,
        }
        self.edgeBottom = {
            "pv_name": "MXSC:Bottom",
            "getter": self.get_edgeBottom_value,
            "value": initial_edgeBottom,
        }

        # put them in a list so we can iterate through and add the getters to the EPICS
        self.EDGE_DETECTION_PVS: list[dict] = [
            self.exposurePV,
            self.acqPeriodPV,
            self.gainPV,
            self.oavColourMode,
            self.xSizePV,
            self.ySizePV,
            self.inputRBPV,
            self.exposureRBPV,
            self.acqPeriodRBPV,
            self.gainRBPV,
            self.inputPV,
            self.enableOverlayPV,
            self.overlayPortPV,
            self.useOverlay1PV,
            self.useOverlay2PV,
            self.overlay2ShapePV,
            self.overlay2RedPV,
            self.overlay2GreenPV,
            self.overlay2BluePV,
            self.overlay2XPosition,
            self.overlay2YPosition,
            self.overlay2XSize,
            self.overlay2YSize,
            self.edgeTop,
            self.edgeBottom,
        ]

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
        return DeviceUpdate(OAVEdgeDetectionDevice.Outputs(), None)

    def get_exposurePV_value(self):
        """For use by EPICs adapter."""
        return self.exposurePV["value"]

    def get_acqPeriodPV_value(self):
        """For use by EPICs adapter."""
        return self.acqPeriodPV["value"]

    def get_gainPV_value(self):
        """For use by EPICs adapter."""
        return self.gainPV["value"]

    def get_oavColourMode_value(self):
        """For use by EPICs adapter."""
        return self.oavColourMode["value"]

    def get_xSizePV_value(self):
        """For use by EPICs adapter."""
        return self.xSizePV["value"]

    def get_ySizePV_value(self):
        """For use by EPICs adapter."""
        return self.ySizePV["value"]

    def get_inputRBPV_value(self):
        """For use by EPICs adapter."""
        return self.inputRBPV["value"]

    def get_exposureRBPV_value(self):
        """For use by EPICs adapter."""
        return self.exposureRBPV["value"]

    def get_acqPeriodRBPV_value(self):
        """For use by EPICs adapter."""
        return self.acqPeriodRBPV["value"]

    def get_gainRBPV_value(self):
        """For use by EPICs adapter."""
        return self.gainRBPV["value"]

    def get_inputPV_value(self):
        """For use by EPICs adapter."""
        return self.inputPV["value"]

    def get_enableOverlayPV_value(self):
        """For use by EPICs adapter."""
        return self.enableOverlayPV["value"]

    def get_overlayPortPV_value(self):
        """For use by EPICs adapter."""
        return self.overlayPortPV["value"]

    def get_useOverlay1PV_value(self):
        """For use by EPICs adapter."""
        return self.useOverlay1PV["value"]

    def get_useOverlay2PV_value(self):
        """For use by EPICs adapter."""
        return self.useOverlay2PV["value"]

    def get_overlay2ShapePV_value(self):
        """For use by EPICs adapter."""
        return self.overlay2ShapePV["value"]

    def get_overlay2RedPV_value(self):
        """For use by EPICs adapter."""
        return self.overlay2RedPV["value"]

    def get_overlay2GreenPV_value(self):
        """For use by EPICs adapter."""
        return self.overlay2GreenPV["value"]

    def get_overlay2BluePV_value(self):
        """For use by EPICs adapter."""
        return self.overlay2BluePV["value"]

    def get_overlay2XPosition_value(self):
        """For use by EPICs adapter."""
        return self.overlay2XPosition["value"]

    def get_overlay2YPosition_value(self):
        """For use by EPICs adapter."""
        return self.overlay2YPosition["value"]

    def get_overlay2XSize_value(self):
        """For use by EPICs adapter."""
        return self.overlay2XSize["value"]

    def get_overlay2YSize_value(self):
        """For use by EPICs adapter."""
        return self.overlay2YSize["value"]

    def get_edgeTop_value(self):
        """For use by EPICs adapter."""
        return self.edgeTop["value"]

    def get_edgeBottom_value(self):
        """For use by EPICs adapter."""
        return self.edgeBottom["value"]


class OAVEdgeDetectionTCPAdapter(ComposedAdapter):
    """A TCP adapter to set a OAVEdgeDetectionDevice PV values."""

    device: OAVEdgeDetectionDevice

    def __init__(
        self,
        server: Server,
    ) -> None:
        """OAV current adapter, instantiates TcpServer with configured host and port.

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


class OAVEdgeDetectionEpicsAdapter(EpicsAdapter):
    """Epics Adapter.

    Epics adapter for reading all EdgeDetectionAttributes as a PV
    through channel access.
    """

    device: OAVEdgeDetectionDevice

    def on_db_load(self) -> None:
        """Link loaded in record with getter for device."""
        for pv in self.device.EDGE_DETECTION_PVS:
            self.link_input_on_interrupt(
                builder.aIn(pv["pv_name"]),
                pv["getter"],
            )


@dataclass
class OAVEdgeDetection(ComponentConfig):
    """Synchrotron current component."""

    initial_exposurePV: float
    initial_acqPeriodPV: float
    initial_gainPV: float
    initial_oavColourMode: float
    initial_xSizePV: float
    initial_ySizePV: float
    initial_inputRBPV: float
    initial_exposureRBPV: float
    initial_acqPeriodRBPV: float
    initial_gainRBPV: float
    initial_inputPV: float
    initial_enableOverlayPV: float
    initial_overlayPortPV: float
    initial_useOverlay1PV: float
    initial_useOverlay2PV: float
    initial_overlay2ShapePV: float
    initial_overlay2RedPV: float
    initial_overlay2GreenPV: float
    initial_overlay2BluePV: float
    initial_overlay2XPosition: float
    initial_overlay2YPosition: float
    initial_overlay2XSize: float
    initial_overlay2YSize: float
    initial_edgeTop: float
    initial_edgeBottom: float
    host: str = "localhost"
    port: int = 25565
    format: ByteFormat = ByteFormat(b"%b\r\n")
    db_file: str = "tickit_devices/oav/db_files/DCCT.db"
    ioc_name: str = "S03-SIM-DI-OAV-01"

    def __call__(self) -> Component:  # noqa: D102
        return DeviceSimulation(
            name=self.name,
            device=OAVEdgeDetectionDevice(
                self.initial_exposurePV,
                self.initial_acqPeriodPV,
                self.initial_gainPV,
                self.initial_oavColourMode,
                self.initial_xSizePV,
                self.initial_ySizePV,
                self.initial_inputRBPV,
                self.initial_exposureRBPV,
                self.initial_acqPeriodRBPV,
                self.initial_gainRBPV,
                self.initial_inputPV,
                self.initial_enableOverlayPV,
                self.initial_overlayPortPV,
                self.initial_useOverlay1PV,
                self.initial_useOverlay2PV,
                self.initial_overlay2ShapePV,
                self.initial_overlay2RedPV,
                self.initial_overlay2GreenPV,
                self.initial_overlay2BluePV,
                self.initial_overlay2XPosition,
                self.initial_overlay2YPosition,
                self.initial_overlay2XSize,
                self.initial_overlay2YSize,
                self.initial_edgeTop,
                self.initial_edgeBottom,
            ),
            adapters=[
                OAVEdgeDetectionTCPAdapter(
                    TcpServer(self.host, self.port, self.format)
                ),
                OAVEdgeDetectionEpicsAdapter(self.db_file, self.ioc_name),
            ],
        )
