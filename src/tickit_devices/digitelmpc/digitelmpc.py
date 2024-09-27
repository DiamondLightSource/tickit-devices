import asyncio

from typing import TypedDict, AsyncIterable
from tickit.core.device import Device, DeviceUpdate


from tickit.adapters.specifications import RegexCommand
from tickit.adapters.tcp import CommandAdapter
from tickit.core.typedefs import SimTime

from tickit_devices.digitelmpc.base import DigitelMpcBase
from tickit_devices.digitelmpc.states import Status

class DigitelMpcDevice(Device,DigitelMpcBase):
    """Ion pump vacuum controller device."""

    class Inputs(TypedDict):
        ...

    class Outputs(TypedDict):
        pressure: float

    def __init__(self,) -> None:
        """A digitelMpc constructor that sets up initial internal values."""

        super().__init__()
        self.status: int = Status.RUNNING.value
        # self.callback_period: SimTime = SimTime(int(1e9))

    def update(self, time: SimTime, inputs : Inputs) -> DeviceUpdate[Outputs]:
        """The update method which changes the pressure according to set modes.
        
        Returns:
            DeviceUpdate[Outputs]:
                The produced update event which contains the value of the output
                pressure, and requests callback if pressure should continue to
                change.
        
        """

        return DeviceUpdate(self.Outputs(pressure=self.pressure), None)
    

class DigitelMpcAdapter(CommandAdapter):
    """A digitelMpc TCP adapter which sends regular status packets and can set modes."""

    device: DigitelMpcDevice

    def __init__(self, device: DigitelMpcDevice) -> None:
        super().__init__()
        self.device = device


    async def on_connect(self) -> AsyncIterable[bytes]:
        """A method which continously yields status packets.
        
            Returns:
                AsyncIterable[bytes]: An asynchronous iterable of packed diitelMpc status 
                    packets.
        """
        # while True:
        #     await asyncio.sleep(2.0)
        #     # await self.device
        #     pass

    @RegexCommand(r"~ 01 01 22", interrupt=False, format="utf-8")
    async def get_model_name(self) -> None:
        """A regex bytes command which gets model name """
        return str("01 OK 00 DIGITEL MPCQ 0E").encode("utf-8")

    @RegexCommand(r"~ 01 01 37", interrupt=False, format="utf-8")
    async def start(self) -> None:
        """A regex bytes command that initialises the controller"""
        await self.device.start()
        return str("01 OK 00 00").encode("utf-8")
    
    @RegexCommand(r"~ 01 0B 01 B4", interrupt=False, format="utf-8")
    async def get_pressure(self) -> None:
        """A regex bytes commmand which gets the current pressure of the system"""
        pressure = await self.device.get_pressure()
        return str(f"01 OK 00 {pressure} TORR A5").encode("utf-8")
    
    @RegexCommand(r"~ 01 12 (?P<pump_size>\d+) 00", interrupt=False, format="utf-8")
    async def set_pump_size(self, pump_size: float) -> None:
        """A regex bytes command which sets the pump size"""
        await self.device.set_pump_size(pump_size)
        return str("01 OK 00 00").encode("utf-8")
    
    @RegexCommand(r"~ 01 11 02 B5", interrupt=False, format="utf-8")
    async def get_pump_size(self) -> None:
        """A regex btyes command which gets the current pump size"""
        pump_size = await self.device.get_pump_size()
        return str(f"01 OK 00 {pump_size} L/S A6").encode("utf-8")
    
    @RegexCommand(r"~ 01 0A 01 B3", interrupt=False, format="utf-8")
    async def get_current(self) -> None:
        """A regex bytes commmand which gets the current pressure of the system"""
        current = await self.device.get_current()
        return str(f"01 OK 00 {current} AMPS C5").encode("utf-8")
    
    @RegexCommand(r"~ 01 0C 01 B5", interrupt=False, format="utf-8")
    async def get_voltage(self) -> None:
        """A regex bytes command which gets the voltage"""
        voltage = await self.device.get_voltage()
        return str(f"01 OK 00 {voltage} VOLTS C").encode("utf-8")
    
    @RegexCommand(r"~ 01 22 (?P<voltage>\d+) 00", interrupt=False, format="utf-8")
    async def set_voltage(self, voltage: float) -> None:
        """A regex bytes command which sets the pump size"""
        await self.device.set_voltage(voltage)
        return str("01 OK 00 00").encode("utf-8") 

    @RegexCommand(r"~ 01 FF 01 CE", interrupt=False, format="utf-8")
    async def reset(self) -> None:
        """A regex command that resets the state of the controller"""
        await self.device.reset()

    @RegexCommand(r"~ 01 0D 01 B6", interrupt=False, format="utf-8")
    async def get_pump_status(self)-> None:
        """A regex command that gets the status of the pump"""
        status = await self.device.get_pump_status()
        return str(f"01 OK 00 0{status}").encode("utf-8")