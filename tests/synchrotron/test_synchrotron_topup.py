import pytest
from tickit.core.device import DeviceUpdate
from tickit.core.typedefs import SimTime

from tickit_devices.synchrotron.synchrotron_topup import SynchrotronTopUpDevice

COUNTDOWN = 600
ENDCOUNTDN = 620


@pytest.fixture
def synchrotron_topup() -> SynchrotronTopUpDevice:
    return SynchrotronTopUpDevice(
        initial_countdown=COUNTDOWN,
        initial_end_countdown=ENDCOUNTDN,
        callback_period=int(1e9),
    )


def test_synchrotron_topup_constructor(
    synchrotron_topup: SynchrotronTopUpDevice,
):
    pass


def test_synchrotron_topup_get_countdown(
    synchrotron_topup: SynchrotronTopUpDevice,
):
    synchrotron_topup.countdown = COUNTDOWN
    assert synchrotron_topup.get_countdown() == COUNTDOWN


def test_synchrotron_topup_update_new_countdown(
    synchrotron_topup: SynchrotronTopUpDevice,
):
    device_update: DeviceUpdate = synchrotron_topup.update(
        SimTime(0), inputs={"current": 299.95}
    )

    countdown = (299.95 - 270) / 0.05

    # countdown seconds need to be rounded since the scheduler introduces slight changes
    # many decimal places in
    assert round(device_update.outputs["countdown"], -7) == round(countdown, -7)
    assert round(device_update.outputs["end_countdown"], -7) == round(
        countdown + 15, -7
    )


def test_synchrotron_topup_update_new_countdown_topup_fill():
    synchrotron_topup = SynchrotronTopUpDevice(last_current=290)
    device_update: DeviceUpdate = synchrotron_topup.update(
        SimTime(0), inputs={"current": 291}
    )

    countdown = (300 - 291) / (291 - 290)

    # countdown seconds need to be rounded since the scheduler introduces slight changes
    # many decimal places in
    assert device_update.outputs["countdown"] == 0
    assert device_update.outputs["end_countdown"] == countdown


def test_synchrotron_topup_call_at(synchrotron_topup: SynchrotronTopUpDevice):
    device_update: DeviceUpdate = synchrotron_topup.update(
        SimTime(0), inputs={"current": 289}
    )
    expected_output = int(1e9)
    assert device_update.call_at == expected_output
