from tickit_devices.merlin.detector import MerlinDetector
from tickit_devices.merlin.parameters import commands, CommandType, MerlinParameter, ColourMode
from tickit_devices.merlin.acq_header import ACQ_HEADER_SIZE
import pytest

@pytest.fixture
def merlin():
    merlin = MerlinDetector()
    merlin.initialise()
    return merlin

def test_uninitialised_merlin_no_parameters():
    merlin = MerlinDetector()
    assert not merlin.commands
    assert not merlin.parameters

def test_initialised_merlin_has_all_parameters(merlin: MerlinDetector):
    for parameter in list(commands[CommandType.GET]) + list(commands[CommandType.SET]):
        assert parameter in merlin.parameters
    for command in commands[CommandType.CMD]:
        assert command in merlin.commands

def test_image_size_correct(merlin):
    assert len(merlin.chips) == 4  # quad configuration by default
    # should be size of acq header + frame header + image data
    image = merlin.get_image()
    # default header size is 768 + 15
    # default bytes per pixel is 2 for 12 bit mode
    frame_size = (15 + 768 + 515 * 515 * 2)
    assert len(image) == 15 + ACQ_HEADER_SIZE + frame_size

    # the next image won't have an acquisition header
    image = merlin.get_image()
    assert len(image) == frame_size

    merlin._current_frame = 1

    # when getting colour images, all are sent together
    merlin.set_colour_mode(ColourMode.COLOUR)
    # now 1 acquisition header, 8 frame headers and 8 frames, at lower resolution
    image = merlin.get_image()
    expected_size = 15 + ACQ_HEADER_SIZE + 8 * (15 + 768 + 257 * 257 * 2)
    assert len(image) == expected_size

def test_resolution(merlin):
    # quad configuration by default
    merlin.set_colour_mode(ColourMode.MONOCHROME)
    assert merlin.get_resolution() == (515, 515)
    merlin.set_colour_mode(ColourMode.COLOUR)
    assert merlin.get_resolution() == (257, 257)
    
    merlin.gap = False
    
    merlin.set_colour_mode(ColourMode.MONOCHROME)
    assert merlin.get_resolution() == (512, 512)
    merlin.set_colour_mode(ColourMode.COLOUR)
    assert merlin.get_resolution() == (256, 256)

    merlin.gap = True

    for idx, chip in enumerate(merlin.chips):
        if idx > 0:  # single chip
            chip.enabled = False
    merlin.set_colour_mode(ColourMode.MONOCHROME)
    assert merlin.get_resolution() == (256, 256)
    merlin.set_colour_mode(ColourMode.COLOUR)
    assert merlin.get_resolution() == (128, 128)
