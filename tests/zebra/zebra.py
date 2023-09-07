import pytest
from tickit.core.typedefs import ComponentID, SimTime

from tickit_devices.zebra.and_or_block import AndOrBlock

all_true = 15
one_false = 14
one_true = 1
all_false = 0
varying_values_of_true = {all_false, one_true, one_false, all_true}


# # # # # AndOrBlock Tests # # # # #


@pytest.mark.parametrize("enabled", varying_values_of_true)
@pytest.mark.parametrize("inverted", varying_values_of_true)
def test_and_block_enabled_or_inverted(enabled: int, inverted: int):
    name = ComponentID("AND1")
    mux = {f"INP{i + 1}": True for i in range(4)}
    block = AndOrBlock(name=name)
    block.params = {f"{name}_ENA": enabled, f"{name}_INV": inverted}
    out = block.update(SimTime(0), mux)
    assert out.outputs == {
        "OUT": enabled + inverted == all_true
    }  # All devices either enabled or inverted


@pytest.mark.parametrize("enabled", varying_values_of_true)
@pytest.mark.parametrize("inverted", varying_values_of_true)
def test_or_block_enabled_or_inverted(enabled: int, inverted: int):
    name = ComponentID("OR1")
    block = AndOrBlock(name=name)
    block.params = {f"{name}_ENA": enabled, f"{name}_INV": inverted}
    mux = {f"INP{i + 1}": True for i in range(4)}
    out = block.update(SimTime(0), mux)
    assert out.outputs == {
        "OUT": enabled != inverted
    }  # At least one device exclusively enabled or inverted


@pytest.mark.parametrize("high", varying_values_of_true)
def test_all_enabled_and_block_for_inputs(high: int):
    name = ComponentID("AND1")
    block = AndOrBlock(name=name)
    block.params = {f"{name}_ENA": all_true, f"{name}_INV": all_false}
    mux = {f"INP{i + 1}": bool(high & (1 << i)) for i in range(4)}
    out = block.update(SimTime(0), mux)
    assert out.outputs == {"OUT": high == all_true}  # All inputs high


@pytest.mark.parametrize("high", varying_values_of_true)
def test_all_enabled_or_block_for_inputs(high: int):
    name = ComponentID("OR1")
    block = AndOrBlock(name=name)
    block.params = {f"{name}_ENA": all_true, f"{name}_INV": all_false}
    mux = {f"INP{i + 1}": bool(high & (1 << i)) for i in range(4)}
    out = block.update(SimTime(0), mux)
    assert out.outputs == {"OUT": high != all_false}  # At least one input high
