import pytest

from tickit_devices.eiger.filewriter.filewriter_config import FileWriterConfig

# # # # # Eiger FileWriterConfig Tests # # # # #


@pytest.fixture
def filewriter_config() -> FileWriterConfig:
    return FileWriterConfig()


def test_eiger_filewriter_config_constructor():
    FileWriterConfig()


def test_eiger_filewriter_config_get_set(filewriter_config):
    assert "enabled" == filewriter_config["mode"]["value"]
    filewriter_config["mode"] = "disabled"
    assert "disabled" == filewriter_config["mode"]["value"]

    with pytest.raises(ValueError):
        filewriter_config["doesnt_exist"]
