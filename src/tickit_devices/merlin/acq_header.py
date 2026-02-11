from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tickit_devices.merlin.detector import MerlinDetector

ACQ_HEADER_SIZE = 2049


def get_acq_header(merlin: "MerlinDetector"):

    dac_string = ";\n".join(
        [chip.get_dac_string() for chip in merlin.chips if chip.enabled]
    )
    counter_mode = merlin.get("ENABLECOUNTER1")
    if counter_mode == 0:
        counter_string = "Counter 0"
    elif counter_mode == 1:
        counter_string = "Counter 1"
    else:  # assume == 2
        counter_string = "Counter 0 & Counter 1"
    fill_mode = merlin.get("FILLMODE")
    if fill_mode == 0:
        fill_string = "None"
    elif fill_mode == 1:
        fill_string = "Zero Fill"
    elif fill_mode == 2:
        fill_string = "Distribute"
    else:
        fill_string = "Interpolate"
    acquisition_header = (
        f"""MPX,{ACQ_HEADER_SIZE:010},HDR,
Time and Date Stamp (day, mnth, yr, hr, min, s):	{
    datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
Chip ID:	{", ".join([chip.get_id_for_header() for chip in merlin.chips])}
Chip Type (Medipix 3.0, Medipix 3.1, Medipix 3RX):	{merlin.chip_type}
Assembly Size (NX1, 2X2):	   {merlin.get_configuration()}
Chip Mode  (SPM, CSM, CM, CSCM):	{merlin.chips[0].mode}
Counter Depth (number):	{merlin.get("COUNTERDEPTH")}
Gain:	{merlin.get("GAIN")}
Active Counters:	{counter_string}
Thresholds (keV):	{merlin.chips[0].get_threshold_string_scientific()}
DACs:	{dac_string}
bpc File:	{",".join(chip.bpc_file for chip in merlin.chips)}
DAC File:	{",".join(chip.dac_file for chip in merlin.chips)}
Gap Fill Mode:	{fill_string}
Flat Field File:	{merlin.get("FLATFIELDFILE")}
Dead Time File:	{merlin.dead_time_file}
Acquisition Type (Normal, Th_scan, Config):	{merlin.acq_type}
Frames in Acquisition (Number):	{merlin.get("NUMFRAMESTOACQUIRE")}
Frames per Trigger (Number):	{merlin.get("NUMFRAMESPERTRIGGER")}
Trigger Start (Positive, Negative, Internal):	{
    ["Positive", "Negative", "Internal"][merlin.get("TRIGGERSTART").value]}
Trigger Stop (Positive, Negative, Internal):	{
    ["Positive", "Negative", "Internal"][merlin.get("TRIGGERSTOP").value]}
Sensor Bias (V):	{merlin.get("HVBIAS")} V
Sensor Polarity (Positive, Negative):	{merlin.get("POLARITY")}
Temperature (C):	Board Temp {merlin.get("TEMPERATURE"):.6f} Deg C
Humidity (%):	Board Humidity {merlin.humidity:.6f}
Medipix Clock (MHz):	{merlin.medipix_clock}MHz
Readout System:	{merlin.readout_system}
Software Version:	{merlin.get("SOFTWAREVERSION")}
End
"""
    ).ljust(ACQ_HEADER_SIZE + len(f"MPX,{ACQ_HEADER_SIZE:010},"))
    return acquisition_header
