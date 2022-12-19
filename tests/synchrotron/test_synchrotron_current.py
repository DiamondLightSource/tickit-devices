import pytest
from tickit.core.device import DeviceUpdate
from tickit.core.typedefs import SimTime

from tickit_devices.synchrotron.synchrotron_current import SynchrotronCurrentDevice

INITIAL_CURRENT = 300


@pytest.fixture
def synchrotron_current() -> SynchrotronCurrentDevice:
    return SynchrotronCurrentDevice(initial_current=INITIAL_CURRENT)


def test_synchrotron_current_constructor(synchrotron_current: SynchrotronCurrentDevice):
    pass


def test_synchrotron_current_set_and_get_current(
    synchrotron_current: SynchrotronCurrentDevice,
):
    synchrotron_current.beam_current = INITIAL_CURRENT
    assert synchrotron_current.get_current() == INITIAL_CURRENT


def test_synchrotron_current_lose_current_update(
    synchrotron_current: SynchrotronCurrentDevice,
):
    loss_increment = (270 - INITIAL_CURRENT) / 600
    expected_output = INITIAL_CURRENT + loss_increment
    device_update: DeviceUpdate = synchrotron_current.update(SimTime(0), inputs={})
    assert device_update.outputs["current"] == expected_output


def test_synchrotron_current_topup_fill_update():
    INITIAL_CURRENT = 239
    fill_incremenet = (300 - 270) / 15
    expected_output = INITIAL_CURRENT + fill_incremenet
    device_update: DeviceUpdate = SynchrotronCurrentDevice(
        initial_current=INITIAL_CURRENT
    ).update(SimTime(0), inputs={})
    assert device_update.outputs["current"] == expected_output


def test_synchrotron_current_topup_fill_stops():
    INITIAL_CURRENT = 268
    fill_incremenet = (300 - 270) / 15
    expected_output = INITIAL_CURRENT + fill_incremenet
    device = SynchrotronCurrentDevice(initial_current=INITIAL_CURRENT)
    device_update: DeviceUpdate = device.update(SimTime(0), inputs={})
    assert device_update.outputs["current"] == expected_output

    # mimick a topup for 15 seconds then check the current starts depleting again
    i = 0
    while i < 15:
        i += 1
        new_device_update: DeviceUpdate = device.update(
            SimTime(int(1e9) * i), inputs={}
        )

        assert new_device_update.outputs["current"] > device_update.outputs["current"]
        device_update = new_device_update

    i += 1
    assert (
        device.update(SimTime(int(1e9) * i), inputs={}).outputs["current"]
        < device_update.outputs["current"]
    )


def test_synchrotron_current_call_at(synchrotron_current: SynchrotronCurrentDevice):
    device_update: DeviceUpdate = synchrotron_current.update(SimTime(0), inputs={})
    expected_output = int(1e9)
    assert device_update.call_at == expected_output
