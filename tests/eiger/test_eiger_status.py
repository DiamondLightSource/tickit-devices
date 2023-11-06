import pytest

from tickit_devices.eiger.eiger_status import EigerStatus

# # # # # EigerStatus Tests # # # # #


@pytest.fixture
def eiger_status() -> EigerStatus:
    return EigerStatus()


def test_eiger_status_constructor():
    EigerStatus()


def test_eiger_status_getitem(eiger_status):
    assert 24.5 == eiger_status["th0_temp"]["value"]

    with pytest.raises(ValueError):
        eiger_status["doesnt_exist"]
