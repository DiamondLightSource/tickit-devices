"""smargon_motor_fetcher.py, for passing the smargon angle into oav_edge_detection.py.

oav_edge_detection.py requires the omega angle of the S03 motor to set the
current waveform based on. We can't pass this in from S03, so this temporary
solution will create a device which monitors BL03S-MO-SGON-01:[X, Y, Z, OMEGA]
for changes and outputs them to the edge detection tickit device.
"""

from dataclasses import dataclass

from cothread.catools import caget
from tickit.core.components.component import Component, ComponentConfig
from tickit.core.components.device_simulation import DeviceSimulation
from tickit.core.device import Device, DeviceUpdate
from tickit.core.typedefs import SimTime
from tickit.utils.compat.typing_compat import TypedDict


@dataclass
class SmargonGetter(ComponentConfig):

    name: str
    callback_period: int = int(1e9)

    def __call__(self) -> Component:  # noqa: D102
        return DeviceSimulation(
            name=self.name,
            device=SmargonGetterDevice(callback_period=self.callback_period),
        )


class SmargonGetterDevice(Device):
    """A trivial toy device which produced a random output and requests a callback."""

    #: An empty typed mapping of device inputs
    Inputs: TypedDict = TypedDict("Inputs", {})
    #: A typed mapping containing the 'output' output value
    Outputs: TypedDict = TypedDict(
        "Outputs", {"x": float, "y": float, "z": float, "omega": float}
    )

    def __init__(self, callback_period: int = int(1e9)) -> None:
        """A constructor of the sink which configures the device callback period.

        Args:
            callback_period (int): The simulation time callback period of the device
                (in nanoseconds). Defaults to int(1e9).
        """
        self.callback_period = SimTime(callback_period)

    def fetch_omega(self) -> None:
        self.omega = caget("BL03S-MO-SGON-01:OMEGA")

    def fetch_x(self) -> None:
        self.x = caget("BL03S-MO-SGON-01:X")

    def fetch_y(self) -> None:
        self.y = caget("BL03S-MO-SGON-01:Y")

    def fetch_z(self) -> None:
        self.z = caget("BL03S-MO-SGON-01:Z")

    def update(self, time: SimTime, inputs: Inputs) -> DeviceUpdate[Outputs]:
        """The update method which produces a random output and requests a callback.

        The update method which prints the time of the update, the inputs and the
        output which will be produced then returns the random output value and a
        request to be called back after the configured callback period.

        Args:
            time (SimTime): The current simulation time (in nanoseconds).
            inputs (State): A mapping of inputs to the device and their values.

        Returns:
            DeviceUpdate[Outputs]:
                The produced update event which contains the value of the random output,
                and requests a callback after the configured callback period.
        """
        self.fetch_omega()
        self.fetch_x()
        self.fetch_y()
        self.fetch_z()
        return DeviceUpdate(
            SmargonGetterDevice.Outputs(omega=self.omega, x=self.x, y=self.y, z=self.z),
            SimTime(time + self.callback_period),
        )
