import pytest
from tickit.core.device import DeviceUpdate
from tickit.core.typedefs import SimTime

from tickit_devices.eiger.eiger import EigerDevice
from tickit_devices.eiger.eiger_status import State


@pytest.fixture
def eiger() -> EigerDevice:
    return EigerDevice()


def test_eiger_constructor():
    EigerDevice()


def test_starting_state_is_na(eiger: EigerDevice):
    assert_in_state(eiger, State.NA)


@pytest.mark.asyncio
async def test_initialize(eiger: EigerDevice):
    await eiger.initialize()
    assert_in_state(eiger, State.IDLE)


@pytest.mark.asyncio
@pytest.mark.skip
async def test_rejects_command_before_initialize(eiger: EigerDevice):
    await eiger.arm


@pytest.mark.asyncio
async def test_arm(eiger: EigerDevice):
    await eiger.initialize()
    await eiger.arm()
    assert_in_state(eiger, State.READY)


@pytest.mark.asyncio
async def test_disarm(eiger: EigerDevice):
    await eiger.initialize()
    await eiger.arm()
    await eiger.disarm()
    assert_in_state(eiger, State.IDLE)


@pytest.mark.asyncio
async def test_trigger_in_ints_mode_sets_acquire(eiger: EigerDevice):
    await eiger.initialize()
    eiger.settings.trigger_mode = "ints"
    await eiger.arm()
    assert_in_state(eiger, State.READY)
    await eiger.trigger()
    assert_in_state(eiger, State.ACQUIRE)


@pytest.mark.asyncio
async def test_trigger_in_ints_mode_while_not_armed_is_ignored(
    eiger: EigerDevice,
):
    await eiger.initialize()
    eiger.settings.trigger_mode = "ints"
    await eiger.trigger()
    assert_in_state(eiger, State.IDLE)


@pytest.mark.asyncio
async def test_trigger_in_exts_mode_is_ignored(eiger: EigerDevice):
    await eiger.initialize()
    eiger.settings.trigger_mode = "exts"
    await eiger.arm()
    assert_in_state(eiger, State.READY)
    await eiger.trigger()
    assert_in_state(eiger, State.READY)


@pytest.mark.asyncio
async def test_trigger_in_exts_mode_while_not_armed_is_ignored(
    eiger: EigerDevice,
):
    await eiger.initialize()
    eiger.settings.trigger_mode = "exts"
    await eiger.trigger()
    assert_in_state(eiger, State.IDLE)


@pytest.mark.asyncio
async def test_cancel(eiger: EigerDevice):
    await eiger.cancel()
    assert_in_state(eiger, State.READY)


@pytest.mark.asyncio
async def test_abort(eiger: EigerDevice):
    await eiger.abort()
    assert_in_state(eiger, State.IDLE)


@pytest.mark.asyncio
async def test_eiger_acquire_frame_in_ints_mode(eiger: EigerDevice):
    await eiger.initialize()
    eiger.settings.trigger_mode = "ints"
    await eiger.arm()
    await eiger.trigger()

    eiger.update(SimTime(0.0), {})
    eiger.update(SimTime(0.0), {})

    armed, data, end = eiger.consume_data()
    assert len(armed) == 2
    assert len(data) == 4
    assert len(end) == 1


def test_eiger_update_acquiring(eiger: EigerDevice):
    eiger._set_state(State.ACQUIRE)

    eiger._num_frames_left = 1

    time = SimTime(int(1e8))
    device_input = {"bleep", "bloop"}

    update: DeviceUpdate = eiger.update(time, device_input)
    assert update.outputs == {}


def test_eiger_update_acquiring_no_frames_left(eiger: EigerDevice):
    eiger._set_state(State.ACQUIRE)
    eiger._num_frames_left = 0

    time = None
    device_input = {"bleep", "bloop"}

    update: DeviceUpdate = eiger.update(time, device_input)

    assert_in_state(eiger, State.IDLE)
    assert update.outputs == {}


def assert_in_state(eiger: EigerDevice, state: State) -> None:
    assert state.value == eiger.get_state()["value"]
