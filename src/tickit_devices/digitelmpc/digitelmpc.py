from collections.abc import AsyncIterable
from typing import TypedDict

from tickit.adapters.specifications import RegexCommand
from tickit.adapters.tcp import CommandAdapter
from tickit.core.device import Device, DeviceUpdate
from tickit.core.typedefs import SimTime

from tickit_devices.digitelmpc.base import DigitelMpcBase
from tickit_devices.digitelmpc.states import Status


class DigitelMpcDevice(Device, DigitelMpcBase):
    """Ion pump vacuum controller device."""

    class Inputs(TypedDict): ...

    class Outputs(TypedDict):
        pressure1: float
        pressure2: float

    def __init__(self, port) -> None:
        """A digitelMpc constructor that sets up initial internal values."""

        super().__init__()
        self.status: int = Status.RUNNING.value
        self.port = port
        # self.callback_period: SimTime = SimTime(int(1e9))

    def update(self, time: SimTime, inputs: Inputs) -> DeviceUpdate[Outputs]:
        """The update method which changes the pressure according to set modes.

        Returns:
            DeviceUpdate[Outputs]:
                The produced update event which contains the value of the output
                pressure, and requests callback if pressure should continue to
                change.

        """

        return DeviceUpdate(
            self.Outputs(pressure1=self.pumps[1], pressure2=self.pumps[2]), None
        )


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

    def crc_calc(self, message: str) -> str:
        """Method to generate the CRC for a given message.

        args:
            message(str): Message to calculate CRC for.

        Returns:
            calculated_crc(str): Hex representation of CRC
        """

        # Condition the message by removing leading whitespace and removing ~
        message = message.lstrip()
        message = message.strip("~")
        total = 0

        # Message must end in whitespace
        if message[-1] != " ":
            message = message + " "

        for character in message:
            total += ord(character)

        calculated_crc = hex(total % 256)[2:]
        return calculated_crc.upper().zfill(2)

    @RegexCommand(
        (
            r"(?P<msg>~ "
            + r"(?P<unit>[0-3][0-9]) "
            + r"01 "
            + r")"
            + r"(?P<crc>[0-9A-Fa-f]{2})"
        ),
        interrupt=False,
        format="utf-8",
    )
    async def get_model_name(self, msg: str, unit: str, crc: str) -> None:
        """A regex bytes command which gets model name"""
        if self.crc_calc(msg) == crc:
            response = f"{unit} OK 00 {self.device.model}"
        else:
            response = f"{unit} ER 03 BAD CHECKSUM"
        return str(f"{response} {self.crc_calc(response)}\r").encode("utf-8")

    @RegexCommand(
        (
            r"(?P<msg>~ "
            + r"(?P<unit>[0-3][0-9]) "
            + r"02 "
            + r")"
            + r"(?P<crc>[0-9A-Fa-f]{2})"
        ),
        interrupt=False,
        format="utf-8",
    )
    async def get_fw_ver(self, msg: str, unit: str, crc: str) -> None:
        """A regex bytes command which gets model name"""
        if self.crc_calc(msg) == crc:
            response = f"{unit} OK 00 FIRMWARE VERSION: {self.device.firmware_version}"
        else:
            response = f"{unit} ER 03 BAD CHECKSUM"
        return str(f"{response} {self.crc_calc(response)}\r").encode("utf-8")

    @RegexCommand(
        (
            r"(?P<msg>~ "
            + r"(?P<unit>[0-3][0-9]) "
            + r"37 "
            + r"(?P<pump>[1-2]) "
            + r")"
            + r"(?P<crc>[0-9A-Fa-f]{2})"
        ),
        interrupt=False,
        format="utf-8",
    )
    async def start(self, msg: str, unit: str, pump: int, crc: str) -> None:
        """A regex bytes command that initialises the controller"""
        if self.crc_calc(msg) == crc:
            await self.device.start(pump)
            response = f"{unit} OK 00"
        else:
            response = f"{unit} ER 03 BAD CHECKSUM"
        return str(f"{response} {self.crc_calc(response)}\r").encode("utf-8")

    @RegexCommand(
        (
            r"(?P<msg>~ "
            + r"(?P<unit>[0-3][0-9]) "
            + r"38 "
            + r"(?P<pump>[1-2]) "
            + r")"
            + r"(?P<crc>[0-9A-Fa-f]{2})"
        ),
        interrupt=False,
        format="utf-8",
    )
    async def stop(self, msg: str, unit: str, pump: int, crc: str) -> None:
        """A regex bytes command that initialises the controller"""
        if self.crc_calc(msg) == crc:
            await self.device.stop(pump)
            response = f"{unit} OK 00"
        else:
            response = f"{unit} ER 03 BAD CHECKSUM"
        return str(f"{response} {self.crc_calc(response)}\r").encode("utf-8")

    @RegexCommand(
        (
            r"(?P<msg>~ "
            + r"(?P<unit>[0-3][0-9]) "
            + r"0B "
            + r"(?P<pump>[1-2]) "
            + r")"
            + r"(?P<crc>[0-9A-Fa-f]{2})"
        ),
        interrupt=False,
        format="utf-8",
    )
    async def get_pressure(self, msg: str, unit: str, pump: int, crc: str) -> None:
        """A regex bytes commmand which gets the current pressure of the system"""
        if self.crc_calc(msg) == crc:
            pressure = await self.device.get_pressure(pump)
            response = f"{unit} OK 00 {pressure:.1e} {self.device.units}".upper()
        else:
            response = f"{unit} ER 03 BAD CHECKSUM"
        return str(f"{response} {self.crc_calc(response)}\r").encode("utf-8")

    @RegexCommand(
        (
            r"(?P<msg>~ "
            + r"(?P<unit>[0-3][0-9]) "
            + r"0C "
            + r"(?P<pump>[1-2]) "
            + r")"
            + r"(?P<crc>[0-9A-Fa-f]{2})"
        ),
        interrupt=False,
        format="utf-8",
    )
    async def get_voltage(self, msg: str, unit: str, pump: int, crc: str) -> None:
        """A regex bytes commmand which gets the current pressure of the system"""
        if self.crc_calc(msg) == crc:
            voltage = await self.device.get_voltage(pump)
            response = f"{unit} OK 00 {voltage}"
        else:
            response = f"{unit} ER 03 BAD CHECKSUM"
        return str(f"{response} {self.crc_calc(response)}\r").encode("utf-8")

    @RegexCommand(
        (
            r"(?P<msg>~ "
            + r"(?P<unit>[0-3][0-9]) "
            + r"0A "
            + r"(?P<pump>[1-2]) "
            + r")"
            + r"(?P<crc>[0-9A-Fa-f]{2})"
        ),
        interrupt=False,
        format="utf-8",
    )
    async def get_current(self, msg: str, unit: str, pump: int, crc: str) -> None:
        """A regex bytes commmand which gets the current pressure of the system"""
        if self.crc_calc(msg) == crc:
            current = await self.device.get_current(pump)
            response = f"{unit} OK 00 {current:.1e} AMPS".upper()
        else:
            response = f"{unit} ER 03 BAD CHECKSUM"
        return str(f"{response} {self.crc_calc(response)}\r").encode("utf-8")

    @RegexCommand(
        (
            r"(?P<msg>~ "
            + r"(?P<unit>[0-3][0-9]) "
            + r"11 "
            + r"(?P<pump>[1-2]) "
            + r")"
            + r"(?P<crc>[0-9A-Fa-f]{2})"
        ),
        interrupt=False,
        format="utf-8",
    )
    async def get_size(self, msg: str, unit: str, pump: int, crc: str) -> None:
        """A regex bytes commmand which gets the current pressure of the system"""
        if self.crc_calc(msg) == crc:
            size = await self.device.get_size(pump)
            response = f"{unit} OK 00 {size} L/S"
        else:
            response = f"{unit} ER 03 BAD CHECKSUM"
        return str(f"{response} {self.crc_calc(response)}\r").encode("utf-8")

    @RegexCommand(
        (
            r"(?P<msg>~ "
            + r"(?P<unit>[0-3][0-9]) "
            + r"12 "
            + r"(?P<pump>[1-2]),"
            + r"(?P<size>\d{1,4}) "
            + r")"
            + r"(?P<crc>[0-9A-Fa-f]{2})"
        ),
        interrupt=False,
        format="utf-8",
    )
    async def set_size(
        self, msg: str, unit: str, pump: int, size: int, crc: str
    ) -> None:
        """A regex bytes commmand which gets the current pressure of the system"""
        if self.crc_calc(msg) == crc:
            await self.device.set_size(pump, size)
            response = f"{unit} OK 00"
        else:
            response = f"{unit} ER 03 BAD CHECKSUM"
        return str(f"{response} {self.crc_calc(response)}\r").encode("utf-8")

    @RegexCommand(
        (
            r"(?P<msg>~ "
            + r"(?P<unit>[0-3][0-9]) "
            + r"0D "
            + r"(?P<pump>[1-2])"
            + r"(?:,00)? "
            + r")"
            + r"(?P<crc>[0-9A-Fa-f]{2})"
        ),
        interrupt=False,
        format="utf-8",
    )
    async def get_status(self, msg: str, unit: str, pump: int, crc: str) -> None:
        """A regex bytes commmand which gets the current pressure of the system"""
        if self.crc_calc(msg) == crc:
            status = await self.device.get_status(pump)
            response = f"{unit} OK 00 {status} 00"
        else:
            response = f"{unit} ER 03 BAD CHECKSUM"
        return str(f"{response} {self.crc_calc(response)}\r").encode("utf-8")

    @RegexCommand(
        (
            r"(?P<msg>~ "
            + r"(?P<unit>[0-3][0-9]) "
            + r"ED "
            + r"(?P<pump>[1-2]),"
            + r'"(.*?)" '
            + r")"
            + r"(?P<crc>[0-9A-Fa-f]{2})"
        ),
        interrupt=False,
        format="utf-8",
    )
    async def set_text(
        self, msg: str, unit: str, pump: int, text: str, crc: str
    ) -> None:
        """A regex bytes commmand which gets the current pressure of the system"""
        if self.crc_calc(msg) == crc:
            await self.device.set_text(pump, text)
            response = f"{unit} OK 00"
        else:
            response = f"{unit} ER 03 BAD CHECKSUM"
        return str(f"{response} {self.crc_calc(response)}\r").encode("utf-8")

    @RegexCommand(
        (
            r"(?P<msg>~ "
            + r"(?P<unit>[0-3][0-9]) "
            + r"3D "
            + r"(?P<relay>[1-4]),"
            + r"(?P<pump>[1-2]),"
            + r"(?P<spon>[0-9]+\.[0-9]+E[-+]?[0-9]+),"
            + r"(?P<spoff>[0-9]+\.[0-9]+E[-+]?[0-9]+) "
            + r")"
            + r"(?P<crc>[0-9A-Fa-f]{2})"
        ),
        interrupt=False,
        format="utf-8",
    )
    async def set_sps(
        self,
        msg: str,
        unit: str,
        relay: int,
        pump: int,
        spon: str,
        spoff: str,
        crc: str,
    ) -> None:
        """A regex bytes commmand which gets the current pressure of the system"""
        if self.crc_calc(msg) == crc:
            await self.device.set_sp_relay(relay, float(spon), float(spoff))
            response = f"{unit} OK 00"
        else:
            response = f"{unit} ER 03 BAD CHECKSUM"
        return str(f"{response} {self.crc_calc(response)}\r").encode("utf-8")

    @RegexCommand(
        (
            r"(?P<msg>~ "
            + r"(?P<unit>[0-3][0-9]) "
            + r"3C "
            + r"(?P<relay>[1-4]) "
            + r")"
            + r"(?P<crc>[0-9A-Fa-f]{2})"
        ),
        interrupt=False,
        format="utf-8",
    )
    async def get_sps(self, msg: str, unit: str, relay: int, crc: str) -> None:
        """A regex bytes commmand which gets the current pressure of the system"""
        if self.crc_calc(msg) == crc:
            sps = await self.device.get_sp_relay(relay)
            response = (
                f"{unit} OK 00 {relay},1,{sps[0]:.1e},{sps[1]:.1e},{sps[2]}".upper()
            )
        else:
            response = f"{unit} ER 03 BAD CHECKSUM"
        return str(f"{response} {self.crc_calc(response)}\r").encode("utf-8")

    @RegexCommand(
        (
            r"(?P<msg>~ "
            + r"(?P<unit>[0-3][0-9]) "
            + r"1D "
            + r"(?P<pump>[1-2]) "
            + r")"
            + r"(?P<crc>[0-9A-Fa-f]{2})"
        ),
        interrupt=False,
        format="utf-8",
    )
    async def get_cal(self, msg: str, unit: str, pump: int, crc: str) -> None:
        """A regex bytes commmand which gets the current pressure of the system"""
        if self.crc_calc(msg) == crc:
            cal = await self.device.get_cal(pump)
            response = f"{unit} OK 00 {cal:.2f}"
        else:
            response = f"{unit} ER 03 BAD CHECKSUM"
        return str(f"{response} {self.crc_calc(response)}\r").encode("utf-8")

    @RegexCommand(
        (
            r"(?P<msg>~ "
            + r"(?P<unit>[0-3][0-9]) "
            + r"20 "
            + r"(?P<pump>[1-2]) "
            + r")"
            + r"(?P<crc>[0-9A-Fa-f]{2})"
        ),
        interrupt=False,
        format="utf-8",
    )
    async def get_strapV(self, msg: str, unit: str, pump: int, crc: str) -> None:
        """A regex bytes commmand which gets the current pressure of the system"""
        if self.crc_calc(msg) == crc:
            strapV = await self.device.get_strapV(pump)
            response = f"{unit} OK 00 {strapV}"
        else:
            response = f"{unit} ER 03 BAD CHECKSUM"
        return str(f"{response} {self.crc_calc(response)}\r").encode("utf-8")
