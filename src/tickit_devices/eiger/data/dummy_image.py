from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass
class Image:
    """Dataclass to create a basic Image object."""

    index: int
    hash: str
    dtype: str
    data: bytes
    encoding: str
    shape: tuple[int, int]

    @classmethod
    def create_dummy_image(cls, index: int, shape: tuple[int, int]) -> "Image":
        """Returns an Image object wrapping the dummy blob using the metadata provided.

        Args:
            index (int): The index of the Image in the current acquisition.

        Returns:
            Image: An Image object wrapping the dummy blob.
        """
        data = dummy_image_blob()
        hsh = str(hash(data))
        dtype = "uint16"
        encoding = "bs16-lz4<"
        return Image(index, hsh, dtype, data, encoding, shape)


DUMMY_IMAGE_BLOB_PATH: Path = Path(__file__).parent / "frame_sample"


@lru_cache(maxsize=1)
def dummy_image_blob() -> bytes:
    """Load and cache the dummy image blob.

    Load the raw bytes of a compressed image
    taken from the stream of a real Eiger detector.
    This function is cached so there should be few
    (ideally one) loads per runtime.

    Returns:
        A compressed image as a bytes object.
    """
    with DUMMY_IMAGE_BLOB_PATH.open("rb") as frame_file:
        return frame_file.read()
