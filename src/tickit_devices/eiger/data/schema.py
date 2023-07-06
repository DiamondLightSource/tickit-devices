import json
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

from pydantic import BaseModel, Field
from zmq import Frame

Json = Dict[str, Any]
Sendable = Union[bytes, Frame, memoryview]
MultipartMessage = Iterable[Sendable]


def fmt_json(j: Json):  # noqa: D103
    return json.dumps(j).encode("utf_8")


@dataclass
class HeadedBlob:
    """Blob object for frame header."""

    header: Json
    blob: bytes

    def to_message(self) -> MultipartMessage:  # noqa: D102
        yield fmt_json(self.header)
        yield self.blob


@dataclass
class ImageBlob(HeadedBlob):
    """Blob object for frame data."""

    dimensions: Json
    times: Json

    def to_message(self) -> MultipartMessage:  # noqa: D102
        yield fmt_json(self.header)
        yield fmt_json(self.dimensions)
        yield self.blob
        yield fmt_json(self.times)


@dataclass
class Header:
    """Class for header json."""

    global_header: Json
    global_header_config: Json

    flat_field: Optional[HeadedBlob] = None
    pixel_mask: Optional[HeadedBlob] = None
    countrate: Optional[HeadedBlob] = None

    def to_message(self) -> MultipartMessage:  # noqa: D102
        yield fmt_json(self.global_header)
        yield fmt_json(self.global_header_config)

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
    frame: int
    hash: str
    series: int
    htype: str = "dimage-1.0"


class ImageCharacteristicsHeader(BaseModel):
    encoding: str
    shape: Tuple[int, int]
    size: int
    type: str
    htype: str = "dimage_d-1.0"


class ImageConfigHeader(BaseModel):
    real_time: float
    start_time: float
    stop_time: float
    htype: str = "dconfig-1.0"
