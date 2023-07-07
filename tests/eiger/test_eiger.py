from unittest.mock import ANY

import pytest
from mock import MagicMock
from tickit.core.device import DeviceUpdate
from tickit.core.typedefs import SimTime

from tickit_devices.eiger.eiger import EigerDevice
from tickit_devices.eiger.eiger_status import State
from tickit_devices.eiger.stream.eiger_stream import EigerStream


@pytest.fixture
def mock_stream() -> EigerStream:
    return MagicMock(EigerStream)


@pytest.fixture
def eiger(mock_stream: EigerStream) -> EigerDevice:
    return EigerDevice(stream=mock_stream)


def test_eiger_constructor():
    EigerDevice()


def test_starting_state_is_na(eiger: EigerDevice):
    assert_in_state(eiger, State.NA)


@pytest.mark.asyncio
async def test_initialize(eiger: EigerDevice):
    await eiger.initialize()
    assert_in_state(eiger, State.IDLE)


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
async def test_armed_eiger_starts_series(eiger: EigerDevice, mock_stream: EigerStream):
    await eiger.initialize()
    eiger.settings.trigger_mode = "ints"
    await eiger.arm()
    mock_stream.begin_series.assert_called_once_with(eiger.settings, 1)


@pytest.mark.asyncio
async def test_disarmed_eiger_starts_and_ends_series(
    eiger: EigerDevice, mock_stream: EigerStream
):
    await eiger.initialize()
    eiger.settings.trigger_mode = "ints"
    await eiger.arm()
    await eiger.disarm()
    mock_stream.begin_series.assert_called_once_with(eiger.settings, 1)
    mock_stream.end_series.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_cancelled_eiger_starts_and_ends_series(
    eiger: EigerDevice, mock_stream: EigerStream
):
    await eiger.initialize()
    eiger.settings.trigger_mode = "ints"
    await eiger.arm()
    await eiger.cancel()
    mock_stream.begin_series.assert_called_once_with(eiger.settings, 1)
    mock_stream.end_series.assert_called_once_with(1)


@pytest.mark.asyncio
@pytest.mark.parametrize("num_frames", [0, 1, 2, 10])
async def test_eiger_acquire_frames_in_ints_mode(
    eiger: EigerDevice,
    mock_stream: EigerStream,
    num_frames: int,
):
    await eiger.initialize()
    eiger.settings.trigger_mode = "ints"
    eiger.settings.nimages = num_frames
    await eiger.arm()
    await eiger.trigger()

    # Extra update cleans up state
    for _ in range(num_frames + 1):
        eiger.update(SimTime(0.0), {})

    mock_stream.begin_series.assert_called_once_with(eiger.settings, 1)
    if num_frames > 0:
        mock_stream.insert_image.assert_called_with(ANY, 1)
    assert mock_stream.insert_image.call_count == num_frames
    mock_stream.end_series.assert_called_once_with(1)

    assert_in_state(eiger, State.IDLE)


def assert_in_state(eiger: EigerDevice, state: State) -> None:
    assert state.value == eiger.get_state()["value"]
