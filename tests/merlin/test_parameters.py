import pytest
from tickit_devices.merlin.parameters import MerlinParameter

def test_default_merlin_parameter_with_value():
    param = MerlinParameter(5)
    assert param.get() == 5

    param.set(6)
    assert param.get() == 6

def test_default_merlin_parameter_with_callable():
    def get_twentyfive():
        return 25

    param = MerlinParameter(get_twentyfive)
    assert param.get() == 25
    
    with pytest.raises(RuntimeError):
        param.set(26)

def test_merlin_parameter_custom_setter():
    backing_value = 5
    def set_double_what_i_ask_for(value):
        nonlocal backing_value
        backing_value = 2 * value
    
    param = MerlinParameter(lambda: backing_value, set_double_what_i_ask_for)
    assert param.get() == 5
    param.set(6)
    assert param.get() == 12