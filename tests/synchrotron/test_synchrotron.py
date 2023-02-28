import pytest
from aioca import caget

USER_MODE = 4


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "tickit_process", ["examples/configs/synchrotron/synchrotron.yaml"], indirect=True
)
async def test_synchrotron_system(tickit_process):
    assert (await caget("BL03S-CS-CS-MSTAT-01:MODE")) == USER_MODE
