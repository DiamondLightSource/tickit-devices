import pytest
from tickit.core.device import DeviceUpdate
from tickit.core.typedefs import SimTime

from tickit_devices.synchrotron.synchrotron_current import SynchrotronCurrentDevice

INITIAL_CURRENT = 400


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


def test_synchrotron_current_update(synchrotron_current: SynchrotronCurrentDevice):
    device_update: DeviceUpdate = synchrotron_current.update(SimTime(0), inputs={})
    assert device_update.outputs["current"] == INITIAL_CURRENT
    assert device_update.call_at is None
