import pytest
from tickit.core.typedefs import ComponentID, SimTime

from tickit_devices.zebra import ZebraDevice
from tickit_devices.zebra.and_or_block import AndOrBlockConfig


@pytest.fixture
def zebra() -> ZebraDevice:
    return ZebraDevice(ComponentID("zebra"))


all_true = 15
one_false = 14
one_true = 1
all_false = 0
varying_values_of_true = {all_false, one_true, one_false, all_true}


# # # # # AndOrBlock Tests # # # # #
# TODO: Block system tests

@pytest.mark.parametrize("enabled", varying_values_of_true)
@pytest.mark.parametrize("inverted", varying_values_of_true)
def test_all_true(enabled: int, inverted: int):
    name = ComponentID("AND1")
    params = {f"{name}_ENA": enabled, f"{name}_INV": inverted}
    mux = {f"INP{i+1}": True for i in range(4)}
    block = AndOrBlockConfig(name, params)()
    out = block.on_tick(SimTime(0), mux)
    assert out.outputs == {
        enabled + inverted == all_true
    }  # All devices either enabled or inverted
