from tickit_devices.digitelmpc.states import IonPumpState


class IonPump:
    def __init__(self, pumpNumber: int) -> None:
        self.pumpNumber = pumpNumber
        self.size: int = 300
        self.strapV: int = 5600
        self.status: int = IonPumpState.STANDBY
        self.text: str = ""
        self.current: float = float("1e-13")
        self.pressure: float = float("1e-11")
        self.voltage: int = 0
        self.cal: float = 1.00
        self.spstate = 1

    async def start(self):
        self.status: int = IonPumpState.RUNNING
        self.voltage = 6650
        self.current = float("22e-6")
        self.pressure = float("4.5e-9")

    async def stop(self):
        self.status: int = IonPumpState.STANDBY
        self.voltage = 0
        self.current = float("1e-13")
        self.pressure = float("1e-11")

    async def setSize(self, size):
        self.size = size

    async def set_text(self, text):
        self.text = text
