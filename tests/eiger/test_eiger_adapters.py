import pytest
from pytest_mock import MockerFixture

from tickit_devices.eiger.eiger import EigerDevice
from tickit_devices.eiger.eiger_adapters import EigerRESTAdapter, EigerZMQAdapter


def test_after_update(mocker: MockerFixture) -> None:
    test_data = [b"data", b"some more data"]

    # Mock consume_data to return with data the first time and nothing the second time
    device_mock = mocker.MagicMock()
    device_mock.stream.consume_data.side_effect = [test_data, []]

    zmq_adapter = EigerZMQAdapter(device_mock)
    add_mock = mocker.patch.object(zmq_adapter, "add_message_to_stream")

    # Test after_update only calls add_message_to_stream with non-empty data
    zmq_adapter.after_update()
    add_mock.assert_called_once_with(test_data)
    add_mock.reset_mock()
    zmq_adapter.after_update()
    add_mock.assert_not_called()


@pytest.mark.asyncio
async def test_rest_adapter_404(mocker: MockerFixture):
    eiger_adapter = EigerRESTAdapter(EigerDevice())

    request = mocker.MagicMock()
    request.json = mocker.AsyncMock()

    request.match_info = {"parameter_name": "doesnt_exist"}
    assert (await eiger_adapter.get_config(request)).status == 404
    assert (await eiger_adapter.get_board_000_status(request)).status == 404

    request.json.return_value = {}
    assert (await eiger_adapter.put_config(request)).status == 404

    request.match_info = {"parameter_name": "doesnt_exist", "threshold": "1"}
    assert (await eiger_adapter.get_threshold_config(request)).status == 404
    assert (await eiger_adapter.put_threshold_config(request)).status == 404

    request.match_info = {"param": "doesnt_exist"}
    assert (await eiger_adapter.get_monitor_status(request)).status == 404
    assert (await eiger_adapter.get_monitor_config(request)).status == 404
    assert (await eiger_adapter.put_monitor_config(request)).status == 404
    assert (await eiger_adapter.get_filewriter_status(request)).status == 404
    assert (await eiger_adapter.get_filewriter_config(request)).status == 404
    assert (await eiger_adapter.put_filewriter_config(request)).status == 404
    assert (await eiger_adapter.get_stream_status(request)).status == 404
    assert (await eiger_adapter.get_stream_config(request)).status == 404
    assert (await eiger_adapter.put_stream_config(request)).status == 404

    request.match_info = {"status_param": "doesnt_exist"}
    assert (await eiger_adapter.get_status(request)).status == 404
    assert (await eiger_adapter.get_builder_status(request)).status == 404


@pytest.mark.asyncio
async def test_rest_adapter_command_404(mocker: MockerFixture):
    eiger_adapter = EigerRESTAdapter(EigerDevice())

    request = mocker.MagicMock()
    request.text = mocker.AsyncMock()
    request.json = mocker.AsyncMock()
    request.match_info = {"key": "value"}

    assert (await eiger_adapter.initialize_eiger(request)).status == 404
    assert (await eiger_adapter.arm_eiger(request)).status == 404
    assert (await eiger_adapter.disarm_eiger(request)).status == 404
    assert (await eiger_adapter.trigger_eiger(request)).status == 404
    assert (await eiger_adapter.cancel_eiger(request)).status == 404
    assert (await eiger_adapter.abort_eiger(request)).status == 404
