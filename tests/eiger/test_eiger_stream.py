import pytest

from tickit_devices.eiger.stream.eiger_stream import EigerStream


@pytest.fixture
def filewriter() -> EigerStream:
    return EigerStream()


def test_eiger_stream_constructor():
    EigerStream()
