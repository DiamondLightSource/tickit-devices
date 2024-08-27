import asyncio
import os
import signal
import sys
from subprocess import PIPE, STDOUT, Popen

import pytest
import pytest_asyncio
from tickit.core.management.event_router import InverseWiring
from tickit.core.management.schedulers.master import MasterScheduler
from tickit.core.state_interfaces.state_interface import get_interface
from tickit.utils.configuration.loading import read_configs

# Prevent pytest from catching exceptions when debugging in vscode so that break on
# exception works correctly (see: https://github.com/pytest-dev/pytest/issues/7409)
if os.getenv("PYTEST_RAISE", "0") == "1":

    @pytest.hookimpl(tryfirst=True)
    def pytest_exception_interact(call):
        raise call.excinfo.value

    @pytest.hookimpl(tryfirst=True)
    def pytest_internalerror(excinfo):
        raise excinfo.value


# https://docs.pytest.org/en/latest/example/parametrize.html#indirect-parametrization
@pytest.fixture
def tickit_process(request):
    """Subprocess that runs ``tickit all <config_path>``."""
    config_path: str = request.param
    proc = Popen(
        [sys.executable, "-m", "tickit", "all", config_path],
        stdout=PIPE,
        stderr=STDOUT,
        text=True,
    )
    # Wait for IOC to be up
    while True:
        line = proc.stdout.readline()
        if "complete" in line:
            break
    yield proc
    proc.send_signal(signal.SIGINT)
    print(proc.communicate()[0])


@pytest_asyncio.fixture
async def tickit_task(request):
    """Task that runs ``tickit all <config_path>``."""
    config_path: str = request.param
    configs = read_configs(config_path)
    inverse_wiring = InverseWiring.from_component_configs(configs)
    scheduler = MasterScheduler(inverse_wiring, *get_interface("internal"))
    t = asyncio.Task(
        asyncio.wait(
            [
                asyncio.create_task(c().run_forever(*get_interface("internal")))
                for c in configs
            ]
            + [asyncio.create_task(scheduler.run_forever())]
        )
    )
    # TODO: would like to await all_servers_running() here
    await asyncio.sleep(0.5)
    yield t
    tasks = asyncio.tasks.all_tasks()
    for task in tasks:
        task.cancel()
    try:
        await t
    except asyncio.CancelledError:
        pass
