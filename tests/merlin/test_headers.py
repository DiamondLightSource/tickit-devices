from tickit_devices.merlin.detector import MerlinDetector
from tickit_devices.merlin.acq_header import get_acq_header, ACQ_HEADER_SIZE
import pytest
import os
import re

with open(os.path.dirname(__file__) + "/test_acq_header.txt", "r") as f:
    SAMPLE_ACQ_HEADER = f.read()

with open(os.path.dirname(__file__) + "/test_frame_header.txt", "r") as f:
    SAMPLE_FRAME_HEADER = f.read()

@pytest.fixture
def merlin():
    merlin = MerlinDetector()
    merlin.initialise()
    return merlin


def test_acquisition_header(merlin):
    header = get_acq_header(merlin)
    header_parts = header.split("\n")
    sample_header_parts = SAMPLE_ACQ_HEADER.split("\n")
    assert len(header_parts) == len(sample_header_parts)
    for idx in range(len(header_parts)):
        if "Time and Date Stamp" in header_parts[idx]:
            continue
        assert header_parts[idx] == sample_header_parts[idx]
    
    assert len(header) == 15 + ACQ_HEADER_SIZE

def test_frame_header(merlin):
    header = merlin.get_frame_header().decode()
    header_parts = header.split(",")
    sample_header_parts = SAMPLE_FRAME_HEADER.split(",")
    assert len(header_parts) == len(sample_header_parts)
    for idx in range(len(header_parts)):
        if idx == 11:  # time stamp will have changed
            assert re.match(r"^[\d-]*:\d{2}:\d{2}.\d{6}$", header_parts[idx])
            continue
        elif idx == 126:  # another time stamp format
            assert re.match(r"^[\d-]*T\d{2}:\d{2}:\d{2}.\d{9}Z$", header_parts[idx])
            continue
        assert header_parts[idx] == sample_header_parts[idx], idx

