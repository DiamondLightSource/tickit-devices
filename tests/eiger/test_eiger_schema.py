import pytest

from tickit_devices.eiger.eiger_schema import SequenceComplete
from tickit_devices.utils import serialize


@pytest.mark.parametrize("sequence_id", [1, 2])
def test_sequence_complete_uses_alternative_constructor(sequence_id: int) -> None:
    complete = SequenceComplete.number(sequence_id)
    assert complete.sequence_id == sequence_id


@pytest.mark.parametrize("sequence_id", [1, 2])
def test_sequence_complete_uses_space_in_field_name(sequence_id: int) -> None:
    complete = SequenceComplete.number(sequence_id)
    serialized = serialize(complete)
    assert isinstance(serialized, dict)
    assert serialized["sequence id"] == sequence_id


def test_sequence_complete_uses_alias_only() -> None:
    complete = SequenceComplete.number(1)
    serialized = serialize(complete)
    assert isinstance(serialized, dict)
    assert "sequence_id" not in serialized.keys()
