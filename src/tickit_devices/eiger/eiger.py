import asyncio
import logging
from dataclasses import fields
from queue import Queue
from typing import Any, Iterable, Optional, Sequence

from tickit.core.device import Device, DeviceUpdate
from tickit.core.typedefs import SimTime
from typing_extensions import TypedDict

from tickit_devices.eiger.data.dummy_image import Image
from tickit_devices.eiger.eiger_schema import Value, construct_value
from tickit_devices.eiger.eiger_settings import EigerSettings
from tickit_devices.eiger.filewriter.filewriter_config import FileWriterConfig
from tickit_devices.eiger.filewriter.filewriter_status import FileWriterStatus
from tickit_devices.eiger.monitor.monitor_config import MonitorConfig
from tickit_devices.eiger.monitor.monitor_status import MonitorStatus
from tickit_devices.eiger.stream.eiger_stream import EigerStream

from .eiger_status import EigerStatus, State

LOGGER = logging.getLogger("Eiger")


class EigerDevice(Device):
    """A device class for the Eiger detector."""

    settings: EigerSettings
    status: EigerStatus
    stream: EigerStream

    _num_frames_left: int
    _data_queue: Queue

    #: An empty typed mapping of input values
    Inputs: TypedDict = TypedDict("Inputs", {})
    #: A typed mapping containing the 'value' output value
    Outputs: TypedDict = TypedDict("Outputs", {})

    def __init__(
        self,
        settings: Optional[EigerSettings] = None,
        status: Optional[EigerStatus] = None,
        stream: Optional[EigerStream] = None,
    ) -> None:
        """An Eiger device constructor.

        An Eiger device constructor which configures the default settings and various
        states of the device.
        """
        self.settings = settings or EigerSettings()
        self.status = status or EigerStatus()

        # self.stream_status = StreamStatus()
        # self.stream_config = StreamConfig()
        # self.stream_callback_period = SimTime(int(1e9))
        self.stream = stream or EigerStream(callback_period=SimTime(int(1e9)))

        self.filewriter_status: FileWriterStatus = FileWriterStatus()
        self.filewriter_config: FileWriterConfig = FileWriterConfig()
        self.filewriter_callback_period = SimTime(int(1e9))

        self.monitor_status: MonitorStatus = MonitorStatus()
        self.monitor_config: MonitorConfig = MonitorConfig()
        self.monitor_callback_period = SimTime(int(1e9))

        self._num_frames_left: int = 0
        self._total_frames: int = 0
        self._data_queue: Queue = Queue()
        self._series_id: int = 0

        self._finished_aquisition: Optional[asyncio.Event] = None

    @property
    def finished_aquisition(self) -> asyncio.Event:
        """Property to instanciate an asyncio Event if it hasn't aready been."""
        if self._finished_aquisition is None:
            self._finished_aquisition = asyncio.Event()

        return self._finished_aquisition

    async def initialize(self) -> None:
        """Function to initialise the Eiger."""
        self._set_state(State.IDLE)

    async def arm(self) -> None:
        """Function to arm the Eiger."""
        self._series_id += 1
        self.stream.begin_series(self.settings, self._series_id)
        self._num_frames_left = self.settings.nimages
        self._set_state(State.READY)

    async def disarm(self) -> None:
        """Function to disarm the Eiger."""
        self._set_state(State.IDLE)
        self.stream.end_series(self._series_id)

    async def trigger(self) -> None:
        """Function to trigger the Eiger.

        If the detector is in an external trigger mode, this is disabled as
        this software command interface only works for internal triggers.
        """
        LOGGER.info("Trigger requested")
        trigger_mode = self.settings.trigger_mode

        if self._is_in_state(State.READY) and trigger_mode == "ints":
            self._set_state(State.ACQUIRE)
            LOGGER.info("Now in acquiring mode")
            self.finished_aquisition.clear()
        else:
            LOGGER.info(
                f"Ignoring trigger, state={self._get_state()},"
                f"trigger_mode={trigger_mode}"
            )

    async def cancel(self) -> None:
        """Function to stop the data acquisition.

        Function to stop the data acquisition, but only after the next
        image is finished.
        """
        self._set_state(State.READY)
        self.stream.end_series(self._series_id)

    async def abort(self) -> None:
        """Function to abort the current task on the Eiger."""
        self._set_state(State.IDLE)
        self.stream.end_series(self._series_id)

    def update(self, time: SimTime, inputs: Inputs) -> DeviceUpdate[Outputs]:
        """Update function to update the Eiger.

        Args:
            time (SimTime): The simulation time in nanoseconds.
            inputs (Inputs): A TypedDict of the inputs to the Eiger device.

        Returns:
            DeviceUpdate[Outputs]:
                The produced update event which contains the value of the device
                variables.
        """
        if self._is_in_state(State.ACQUIRE):
            if self._num_frames_left > 0:
                self._acquire_frame()

                return DeviceUpdate(
                    self.Outputs(), SimTime(time + int(self.settings.frame_time * 1e9))
                )
            else:
                self.finished_aquisition.set()

                LOGGER.debug("Ending Series...")
                self._set_state(State.IDLE)
                self.stream.end_series(self._series_id)

        return DeviceUpdate(self.Outputs(), None)

    def _acquire_frame(self) -> None:
        frame_id = self.settings.nimages - self._num_frames_left
        LOGGER.debug(f"Frame id {frame_id}")

        shape = (
            self.settings.x_pixels_in_detector,
            self.settings.y_pixels_in_detector,
        )
        image = Image.create_dummy_image(frame_id, shape)
        self.stream.insert_image(image, self._series_id)
        self._num_frames_left -= 1
        LOGGER.debug(f"Frames left: {self._num_frames_left}")

    def consume_data(self) -> Iterable[Sequence[bytes]]:
        """Function to work through the data queue, yielding anything queued."""
        while not self._data_queue.empty():
            yield self._data_queue.get()

    def get_state(self) -> Value:
        """Returns the current state of the Eiger.

        Returns:
            State: The state of the Eiger.
        """
        state = construct_value(self.status, "state")

        return state

    def _set_state(self, state: State) -> None:
        self.status.state = state

    def _is_in_state(self, state: State) -> bool:
        return self._get_state() is state

    def _get_state(self) -> State:
        return self.status.state
