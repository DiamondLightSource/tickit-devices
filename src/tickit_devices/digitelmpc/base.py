import logging
import asyncio
from ctypes import c_short, c_ubyte, c_ushort
from typing import Union

from tickit_devices.digitelmpc.states import Status, Error, SpRelay

LOGGER = logging.getLogger(__name__)

class DigitelMpcBase:
    """A base class for digitelMpc logic."""

    low_pressure: float = 8.2e-11
    high_pressure: float = 800
    set_point_on: float = 1.0e-08
    set_point_off: float = 2.0e-08
    max_pump_size: int = 1000
    min_pump_size: int = 100
    min_voltage: int = 0
    max_voltage: int = 5000

    def __init__(self) -> None:
        """A digitelMpcBase contructor which assigns initial values"""
        self.current: int = 97e-9
        self.pressure: int = 0
        self.voltage: int = 80
        self.status: int = 0
        self.error_code: int = 0
        self.sp_relay: int = SpRelay.ON.value
        self.pump_size: int = 0
        self.calibration: int = 0

    async def start(self) -> None:
        """Starts the digitelMpc controller"""
        self.status = Status.STARTING.value
        self.error_code = Error.OK.value
        self.pressure = 8.0e-11
        self.status = Status.RUNNING.value

    async def reset(self) -> None:
        """Resets the digitelMpc controller"""
        self.__init__()
        self.status = Status.STARTING.value
        self.status = Status.RUNNING.value

    async def stop(self) -> None:
        """Stops the digitelMpc Controller """
        self.status = Status.STANDBY.value

    async def get_pressure(self) -> None:
        """returns the current pressure of the system"""
        return self.pressure
    
    async def get_current(self) -> None:
        """returns the current of the system"""
        return self.current
    
    async def get_voltage(self) -> None:
        """returns the current voltage of the system"""
        return self.voltage
        
    async def set_pump_size(self, pump_size: int ) -> None:
        """Sets the pump size"""
        if pump_size < self.min_pump_size or pump_size > self.max_pump_size:
            self.status = Status.ERROR.value
        else:
            self.pump_size = pump_size
    
    async def get_pump_size(self) -> None:
        """Returns the pump size"""
        return self.pump_size
    
    async def set_voltage(self, voltage_value: int) -> None:
        """Sets the voltage"""
        if voltage_value < self.min_voltage and voltage_value > self.max_voltage:
            self.status = Status.ERROR.value
        else:
            self.voltage = voltage_value

        if voltage_value < self.min_voltage:
            self.error_code = Error.LOW_VOLTAGE.value

        self.pressure = ((voltage_value)*self.high_pressure)/self.max_voltage


    async def get_pump_status(self) -> None:
        """Gets the current status of the pump controller"""
        return self.status

    async def get_sp_relay(self) -> None:
        """Gets the sp relay status"""
        return self.sp_relay


    async def set_calibration(self, calibration_value: int) -> int:
        
        self.calibration = calibration_value

    async def auto_restart(self, autorestart: int) -> int:

        pass







