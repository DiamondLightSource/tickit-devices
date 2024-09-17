import pytest

from tickit_devices.eiger.monitor.monitor_config import MonitorConfig

# # # # # Eiger MonitorConfig Tests # # # # #


@pytest.fixture
def monitor_config() -> MonitorConfig:
    return MonitorConfig()


def test_eiger_monitor_config_constructor():
    MonitorConfig()


def test_eiger_monitor_config_get_set(monitor_config):
    assert "enabled" == monitor_config["mode"]["value"]
    monitor_config["mode"] = "disabled"
    assert "disabled" == monitor_config["mode"]["value"]

    with pytest.raises(ValueError):
        monitor_config["doesnt_exist"]
