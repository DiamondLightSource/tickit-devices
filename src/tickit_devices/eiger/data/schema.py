<<<<<<< HEAD
from typing import Any, Dict, Iterable, Tuple, Union

from pydantic.v1 import BaseModel
=======
import json
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

from pydantic import BaseModel, Field
>>>>>>> b9b2e0b (Rationalise stream messages into a schema)
from zmq import Frame

Json = Dict[str, Any]
Sendable = Union[bytes, Frame, memoryview]
MultipartMessage = Iterable[Sendable]

DEFAULT_HEADER_TYPE = "dheader-1.0"


class AcquisitionSeriesHeader(BaseModel):
    """Sent before a series of images (and associated headers)."""

    header_detail: str
    series: int
    htype: str = DEFAULT_HEADER_TYPE


class AcquisitionSeriesFooter(BaseModel):
    """Sent at the end of a series of images (and associated headers)."""

    series: int
    htype: str = "dseries_end-1.0"


class AcquisitionDetailsHeader(BaseModel):
    """Describes an additional dataset sent at the beginning of a series.

    Used when header_detail is set to all in AcquisitionSeriesHeader.
    """

    htype: str = DEFAULT_HEADER_TYPE
    shape: Tuple[int, int]
    type: str


<<<<<<< HEAD
class ImageHeader(BaseModel):
    """Sent before a detector image blob.

    Metadata about the acquisition operation.
    """

=======
        details = [self.flat_field, self.pixel_mask, self.countrate]
        for detail in details:
            if detail:
                yield from detail.to_message()


DEFAULT_HEADER_TYPE = "dheader-1.0"


class AcquisitionSeriesHeader(BaseModel):
    header_detail: str
    series: int
    htype: str = DEFAULT_HEADER_TYPE


class AcquisitionSeriesFooter(BaseModel):
    series: int
    htype: str = "dseries_end-1.0"


class AcquisitionDetailsHeader(BaseModel):
    htype: str = DEFAULT_HEADER_TYPE
    shape: Tuple[int, int]
    type: str


class ImageHeader(BaseModel):
>>>>>>> b9b2e0b (Rationalise stream messages into a schema)
    frame: int
    hash: str
    series: int
    htype: str = "dimage-1.0"


class ImageCharacteristicsHeader(BaseModel):
<<<<<<< HEAD
    """Sent before a detector image blob.

    Metadata about the image.
    """

=======
>>>>>>> b9b2e0b (Rationalise stream messages into a schema)
    encoding: str
    shape: Tuple[int, int]
    size: int
    type: str
    htype: str = "dimage_d-1.0"


class ImageConfigHeader(BaseModel):
<<<<<<< HEAD
    """Sent before a detector image blob.

    Describes the metrics on the image acquisition.
    """

=======
>>>>>>> b9b2e0b (Rationalise stream messages into a schema)
    real_time: float
    start_time: float
    stop_time: float
    htype: str = "dconfig-1.0"
