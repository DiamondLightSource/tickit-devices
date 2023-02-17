import subprocess

from tickit_devices import __version__


def test_cli_version():
    cmd = ["tickit-devices", "--version"]
    assert subprocess.check_output(cmd).decode().strip() == __version__
