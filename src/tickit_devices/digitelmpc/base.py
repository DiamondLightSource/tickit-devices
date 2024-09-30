import logging

from tickit_devices.digitelmpc.ionPump import IonPump
from tickit_devices.digitelmpc.states import IonPumpState

LOGGER = logging.getLogger(__name__)


class DigitelMpcBase:
    """A base class for digitelMpc logic."""

    def __init__(self) -> None:
        """A digitelMpcBase contructor which assigns initial values"""
        self.model = "DIGITEL MPCe"
        self.units = "TORR"
        self.firmware_version = "05.07.02"
        self.pumps = [None, IonPump(1), IonPump(2)]
        self.sps = {
            "spon": [
                None,
                float("1.0E-07"),
                float("2.0E-07"),
                float("2.0E-07"),
                float("2.0E-07"),
            ],
            "spoff": [
                None,
                float("1.2E-07"),
                float("2.2E-07"),
                float("2.2E-07"),
                float("2.2E-07"),
            ],
            "spstate": [None, 1, 1, 1, 1],
        }

    async def start(self, pump: int) -> None:
        """Starts ion pump"""
        await self.pumps[pump].start()

    async def stop(self, pump: int) -> None:
        """Starts ion pump"""
        await self.pumps[pump].stop()

    async def get_pressure(self, pump: int) -> None:
        """returns the current pressure of the system"""
        return self.pumps[pump].pressure

    async def get_current(self, pump: int) -> None:
        """returns the current of the system"""
        return self.pumps[pump].current

    async def get_voltage(self, pump: int) -> None:
        """returns the current voltage of the system"""
        return self.pumps[pump].voltage

    async def set_size(self, pump: int, size: int) -> None:
        """Sets the pump size"""
        await self.pumps[pump].setSize(size)

    async def get_size(self, pump: int) -> None:
        """Returns the pump size"""
        return self.pumps[pump].size

    async def set_text(self, pump: int, text: str) -> None:
        """Returns the pump size"""
        await self.pumps[pump].set_text(text)

    async def get_status(self, pump: int) -> None:
        """Gets the current status of the pump controller"""
        return IonPumpState(self.pumps[pump].status).name

    async def set_sp_relay(self, relay: int, spon: float, spoff: float) -> None:
        """Gets the sp relay status"""
        self.sps["spon"][relay] = spon
        self.sps["spoff"][relay] = spoff

    async def get_sp_relay(self, relay: int) -> list:
        """Gets the sp relay status"""
        return [
            self.sps["spon"][relay],
            self.sps["spoff"][relay],
            self.sps["spstate"][relay],
        ]

    async def get_cal(self, pump: int) -> float:
        return self.pumps[pump].cal

    async def get_strapV(self, pump: int) -> int:
        return self.pumps[pump].strapV
