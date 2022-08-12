import pytest
from tickit.core.device import DeviceUpdate
from tickit.core.typedefs import SimTime

from tickit_devices.synchrotron.synchrotron_topup import SynchrotronTopUpDevice

COUNTDOWN = 800
ENDCOUNTDN = 810


@pytest.fixture
def synchrotron_topup() -> SynchrotronTopUpDevice:
    return SynchrotronTopUpDevice(
        initial_countdown=COUNTDOWN, initial_end_countdown=ENDCOUNTDN
    )


def test_synchrotron_topup_constructor(
    synchrotron_topup: SynchrotronTopUpDevice,
):
    pass


def test_synchrotron_topup_set_and_get_countdown(
    synchrotron_topup: SynchrotronTopUpDevice,
):
    synchrotron_topup.countdown = COUNTDOWN
    assert synchrotron_topup.get_countdown() == COUNTDOWN


def test_synchrotron_topup_update(
    synchrotron_topup: SynchrotronTopUpDevice,
):
    device_update: DeviceUpdate = synchrotron_topup.update(SimTime(0), inputs={})
    assert device_update.outputs["countdown"] == COUNTDOWN
    assert device_update.call_at is None
