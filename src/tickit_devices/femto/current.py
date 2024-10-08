from random import uniform
from typing import TypedDict

from tickit.core.device import Device, DeviceUpdate
from tickit.core.typedefs import SimTime


class CurrentDevice(Device):
    """The current configured device."""

    class Inputs(TypedDict): ...

    #: A typed mapping containing the current output value
    class Outputs(TypedDict):
        output: float

    def __init__(self, callback_period: int) -> None:
        """Initialise the current device.

        Args:
            callback_period (Optional[int]): The duration in which the device should \
                next be updated. Defaults to int(1e9).
        """
        self.callback_period = SimTime(callback_period)

    def update(self, time: SimTime, inputs) -> DeviceUpdate[Outputs]:
        """Updates the state of the current device.

        Args:
            time (SimTime): The time of the simulation in nanoseconds.
            inputs (State): The state of the input values of the device.

        Returns:
            DeviceUpdate: A container for the Device's outputs and a callback time.
        """
        output = uniform(100, 200)
        print(f"Output! (delta: {time}, inputs: {inputs}, output: {output})")
        return DeviceUpdate(
            self.Outputs(output=output), SimTime(time + self.callback_period)
        )
