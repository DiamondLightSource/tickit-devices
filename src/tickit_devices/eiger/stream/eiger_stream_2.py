import base64
import logging
from collections.abc import Iterable
from pathlib import Path
from queue import Queue
from typing import Any, TypedDict

import cbor2
import numpy as np
from tickit.core.typedefs import SimTime

from tickit_devices.eiger.data.dummy_image import Image
from tickit_devices.eiger.eiger_settings import EigerSettings
from tickit_devices.eiger.stream.stream2 import stream2_tag_decoder

LOGGER = logging.getLogger(__name__)
DATA_PATH = Path(__file__).parent.parent / "data" / "stream2"
STREAM_SETTINGS_MAP = {
    # Direct Mappings
    "beam_center_x": "beam_center_x",  # These come through as ints for some reason
    "beam_center_y": "beam_center_y",
    "count_time": "count_time",
    "frame_time": "frame_time",
    "sensor_material": "sensor_material",
    "sensor_thickness": "sensor_thickness",
    # TODO: This is broken because it is now a map of thresholds
    # threshold_energy="threshold_energy",
    # Indirect Mappings
    "countrate_correction_enabled": "countrate_correction_applied",
    "detector_description": "description",
    "detector_serial_number": "detector_number",
    "flatfield_enabled": "flatfield_correction_applied",
    "image_size_x": "x_pixels_in_detector",
    "image_size_y": "y_pixels_in_detector",
    "incident_energy": "threshold_energy",
    "incident_wavelength": "wavelength",
    "pixel_mask_enabled": "pixel_mask_applied",
    "pixel_size_x": "x_pixel_size",
    "pixel_size_y": "y_pixel_size",
    "saturation_value": "countrate_correction_count_cutoff",
}
START_ALL_FIELDS = ["flatfield", "pixel_mask", "countrate_correction_lookup_table"]
GONIO_AXES = ["chi", "kappa", "omega", "phi", "two_theta"]


def _load_messages():
    start = image = end = None
    with open(DATA_PATH / "start.cbor", "rb") as f:
        start = cbor2.load(f, tag_hook=stream2_tag_decoder)

    # Populate missing large datasets
    sensor_shape = (start["image_size_y"], start["image_size_x"])
    # we need a base64 encoded array of 4 bit integers, numpy can't provide uint4s
    # we can construct it manually for the trivial zero case
    start["countrate_correction_lookup_table"] = base64.b64encode(65536 // 2 * b"\x00")
    start["flatfield"]["threshold_1"] = base64.b64encode(
        np.prod(sensor_shape) // 2 * b"\x00"  # 2 pixels per byte
    )
    start["pixel_mask"]["threshold_1"] = start["flatfield"]["threshold_1"]  # copy value

    with open(DATA_PATH / "image.cbor", "rb") as f:
        image = cbor2.load(f)
    with open(DATA_PATH / "end.cbor", "rb") as f:
        end = cbor2.load(f)

    return start, image, end


class EigerStream2:
    """Simulation of an Eiger stream."""

    callback_period: SimTime

    _message_buffer: Queue[bytes]

    class Inputs(TypedDict):
        """No inputs."""

    class Outputs(TypedDict):
        """No outputs."""

    def __init__(self, callback_period: int = int(1e9)) -> None:
        """Eiger Stream2 constructor."""
        self.callback_period = SimTime(callback_period)

        self._message_buffer = Queue()

        self._start, self._image, self._end = _load_messages()

    def begin_series(
        self, settings: EigerSettings, series_id: int, header_detail: str
    ) -> None:
        """Send the start message marking the beginning of the acquisition series.

        Args:
            settings: Current detector configuration, a snapshot may be sent with the
                headers.
            series_id: ID for the acquisition series.
            header_detail: Header detail for start message - 'none', 'basic' or 'all'
        """
        if header_detail == "all":
            # Use loaded message in place
            start = self._start
        else:
            # Make a copy with "all" fields removed
            start = {k: v for k, v in self._start.items() if k not in START_ALL_FIELDS}

        # Update message with current state
        start["number_of_images"] = settings.nimages * settings.ntrigger
        for stream_field, setting in STREAM_SETTINGS_MAP.items():
            if stream_field not in start:
                start[stream_field] = getattr(settings, setting)
        for axis in [a for a in GONIO_AXES if a not in start["goniometer"]]:
            # get default values for axes not in start message
            # TODO: Captured cbor start message should have all axes?
            start["goniometer"][axis] = {}
            start["goniometer"][axis]["start"] = float(
                getattr(settings, f"{axis}_start")
            )
            start["goniometer"][axis]["increment"] = float(
                getattr(settings, f"{axis}_increment")
            )

        start["series_id"] = series_id

        self._buffer(cbor_dumps(start))

    def insert_image(self, image: Image, series_id: int) -> None:
        """Send headers and an data blob for a single image.

        Args:
            image: The image with associated metadata
            series_id: ID for the acquisition series.
        """
        self._image["series_id"] = series_id
        self._image["image_id"] = image.index

        self._buffer(cbor_dumps(self._image))

    def end_series(self, series_id: int) -> None:
        """Send footer marking the end of an acquisition series.

        Args:
            series_id: ID of the series to end.
        """
        self._end["series_id"] = series_id
        self._buffer(cbor_dumps(self._end))

    def consume_data(self) -> Iterable[bytes]:
        """Consume all headers and data buffered by other methods.

        Returns:
            Iterable[_Message]: Iterable of headers and data
        """
        while not self._message_buffer.empty():
            message = self._message_buffer.get()
            yield message

    def _buffer(self, message: bytes) -> None:
        self._message_buffer.put_nowait(message)


def cbor_dumps(message: dict[str, Any]) -> bytes:
    """Serialize dictionary to cbor, including headers.

    Args:
        message: Message to be serialized

    """
    return cbor2.dumps(cbor2.CBORTag(55799, message))
