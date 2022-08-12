import pytest
from tickit.core.device import DeviceUpdate
from tickit.core.typedefs import SimTime

from tickit_devices.synchrotron.synchrotron_machine import (
    SynchrotronMachineStatusDevice,
)

MODE = 1
USERCOUNTDN = 200000
BEAMENERGY = 3.2


@pytest.fixture
def synchrotron_machine() -> SynchrotronMachineStatusDevice:
    return SynchrotronMachineStatusDevice(
        initial_mode=MODE, initial_countdown=USERCOUNTDN, initial_energy=BEAMENERGY
    )


def test_synchrotron_machine_constructor(
    synchrotron_machine: SynchrotronMachineStatusDevice,
):
    pass


def test_synchrotron_machine_set_and_get_mode(
    synchrotron_machine: SynchrotronMachineStatusDevice,
):
    synchrotron_machine.synchrotron_mode = MODE
    assert synchrotron_machine.get_mode() == MODE


def test_synchrotron_machine_update(
    synchrotron_machine: SynchrotronMachineStatusDevice,
):
    device_update: DeviceUpdate = synchrotron_machine.update(SimTime(0), inputs={})
    assert device_update.outputs["mode"] == 1
    assert device_update.call_at is None
