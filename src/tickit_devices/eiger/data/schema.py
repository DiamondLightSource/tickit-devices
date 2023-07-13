from typing import Any, Dict, Iterable, Tuple, Union

from pydantic.v1 import BaseModel
from zmq import Frame

Json = Dict[str, Any]
Sendable = Union[bytes, Frame, memoryview]
MultipartMessage = Iterable[Sendable]

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
