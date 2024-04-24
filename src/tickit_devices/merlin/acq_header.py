from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tickit_devices.merlin.merlin import Merlin

ACQ_HEADER_SIZE = 2049


def get_acq_header(merlin: "Merlin"):

    dac_string = ";\n".join(
        [chip.get_dac_string() for chip in merlin.chips if chip.enabled]
    )
    if merlin.counter_mode == 0:
        counter_string = "Counter 0"
    elif merlin.counter_mode == 1:
        counter_string = "Counter 1"
    else:  # assume == 2
        counter_string = "Counter 0 & Counter 1"

    acquisition_header = f"""
    MPX,{ACQ_HEADER_SIZE:010},HDR,	
    Time and Date Stamp (day, mnth, yr, hr, min, s):	{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
    Chip ID:	{", ".join([chip.get_id_for_header() for chip in merlin.chips])}
    Chip Type (Medipix 3.0, Medipix 3.1, Medipix 3RX):	Medipix 3RX
    Assembly Size (NX1, 2X2):	   {merlin.get_configuration()}
    Chip Mode  (SPM, CSM, CM, CSCM):	{merlin.chips[0].mode}
    Counter Depth (number):	{merlin.counter_depth}
    Gain:	{merlin.gain_mode}
    Active Counters:	{counter_string}
    Thresholds (keV):	{merlin.chips[0].get_threshold_string_scientific()}
    DACs:	{dac_string}
    bpc File:	{",".join(chip.bpc_file for chip in merlin.chips)}
    DAC File:	{",".join(chip.dac_file for chip in merlin.chips)}
    Gap Fill Mode:	None
    Flat Field File:	{merlin.flat_field_file}
    Dead Time File:	{merlin.dead_time_file}
    Acquisition Type (Normal, Th_scan, Config):	{merlin.acq_type}
    Frames in Acquisition (Number):	{merlin.frames_in_acquisition}
    Frames per Trigger (Number):	{merlin.frames_per_trigger}
    Trigger Start (Positive, Negative, Internal):	{merlin.trigger_start}
    Trigger Stop (Positive, Negative, Internal):	{merlin.trigger_stop}
    Sensor Bias (V):	{merlin.voltage} V
    Sensor Polarity (Positive, Negative):	{merlin.polarity}
    Temperature (C):	Board Temp {merlin.temperature:.6f} Deg C
    Humidity (%):	Board Humidity {merlin.humidity:.6f}
    Medipix Clock (MHz):	120MHz
    Readout System:	Merlin Quad
    Software Version:	{merlin.version}
    End
    """.ljust(
        ACQ_HEADER_SIZE + len(f"MPX,{ACQ_HEADER_SIZE:010},")
    )
    return acquisition_header
