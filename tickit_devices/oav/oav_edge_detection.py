import random
from dataclasses import dataclass

import numpy as np
from softioc import builder
from tickit.adapters.composed import ComposedAdapter
from tickit.adapters.epicsadapter import EpicsAdapter
from tickit.adapters.interpreters.command import CommandInterpreter, RegexCommand
from tickit.adapters.servers.tcp import TcpServer
from tickit.core.adapter import Server
from tickit.core.components.component import Component, ComponentConfig
from tickit.core.components.device_simulation import DeviceSimulation
from tickit.core.device import Device, DeviceUpdate
from tickit.core.typedefs import SimTime
from tickit.utils.byte_format import ByteFormat
from tickit.utils.compat.typing_compat import TypedDict

_MXSC_WAVEFORM_WIDTH = 1024


class OAVDevice(Device):
    #: An empty typed mapping of device inputs
    Inputs: TypedDict = TypedDict("Inputs", {})
    #: A typed mapping containing the current output value
    Outputs: TypedDict = TypedDict("Outputs", {})

    def __init__(self):
        pass

    def update(
        self, time: SimTime, inputs: Inputs, callback_period=int(1e9)
    ) -> DeviceUpdate[Outputs]:
        """
        The device is only altered by adapters so take no inputs.

        Args:
            time (SimTime): The current simulation time (in nanoseconds).
            inputs (State): A mapping of inputs to the device and their values.

        Returns:
            DeviceUpdate[Outputs]:
                The produced update event.
        """
        return DeviceUpdate(OAVDevice.Outputs(), SimTime(time + callback_period))


class OAVDeviceMXSC(Device):
    """Class for simulating the PVs in OAV relevant to edge detection.

    We won't try and implement any fancy logic (yet). Just get the PVs hosted.
    """

    #: An empty typed mapping of device inputs
    Inputs: TypedDict = TypedDict(
        "Inputs", {"x": float, "y": float, "z": float, "omega": float}
    )
    #: A typed mapping containing the current output value
    Outputs: TypedDict = TypedDict("Outputs", {})

    def __init__(self, callback_period=int(1e9)):
        self.top = np.zeros(1024)
        self.bottom = np.zeros(1024)
        self.tip_x = 0
        self.tip_y = 0
        self.callback_period = SimTime(callback_period)

        # Microns per pixels based on a zoom level of 5x
        self.microns_per_x_pixel = 1.58
        self.microns_per_y_pixel = 1.58

        # We get x, y, z, omega of the smargon from the PVs directly on update.
        self.x, self.y, self.z, self.omega = 0.0, 0.0, 0.0, 0.0

        self.tip_distance_x = random.uniform(50, 100)
        self.tip_distance_y = random.uniform(5, 25)

        # The pin can be inserted at whatever orientation.
        widest_rotation = random.uniform(0, 180)
        self.widest_rotation = (widest_rotation, widest_rotation - 180)
        # Objective centre at the widest rotation.
        self.objective_centre_x = random.uniform(300, 400)
        self.objective_centre_y = random.uniform(500, 600)

        # We arbitrarily decide the widest polynomial should be
        # f(x) = -\frac{1}{360}(x - 180)^2 + 90
        self.widest_point_polynomial = -1 / 360 * (np.arange(0, 340) - 180) ** 2 + 90

        # For smargons, the limits are set to 0 since it can rotate indefinitely
        self.high_limit_travel = 0
        self.low_limit_travel = 0

    def reset_waveform_position(self, x, y, z, omega):
        print("HELLLL")
        horizontal = int(-x * 1e3 / self.microns_per_x_pixel)
        vertical = int(
            (-y * 1e3 / self.microns_per_y_pixel) / np.cos(np.radians(omega))
        )
        print(horizontal)
        print(vertical)

        self.tip_x = horizontal + self.tip_distance_x
        self.tip_y = vertical + self.tip_distance_y
        self.top = np.zeros(1024)
        ln = np.log(np.arange(1, _MXSC_WAVEFORM_WIDTH + 1 - self.tip_x))
        self.top[self.tip_x : _MXSC_WAVEFORM_WIDTH] = ln
        self.bottom = -self.top
        print("HELLLL")
        self.top[self.tip_x :] += self.tip_y
        self.bottom[self.tip_x :] += self.tip_y

    def set_waveform_based_on_omega(self):
        """The pin head is wider if omega is closest to a widest angle."""

        # Get how close omega is to a widest angle.
        # We need to modulo since self.omega could exceed 180
        distance_to_widest = min(
            abs(self.omega - self.widest_rotation[0]) % 180,
            abs(self.omega - self.widest_rotation[1]) % 180,
        )
        bulge = self.widest_point_polynomial * (95 - distance_to_widest) / 90
        self.top[self.tip_x : self.tip_x + 340] = bulge + self.tip_y
        self.bottom[self.tip_x : self.tip_x + 340] = -bulge + self.tip_y

    def update(self, time: SimTime, inputs: Inputs) -> DeviceUpdate[Outputs]:
        """Update method, will be unused since camera PVs won't change value without \
            directly setting them.

        The device is only altered by adapters so take no inputs.

        Args:
            time (SimTime): The current simulation time (in nanoseconds).
            inputs (State): A mapping of inputs to the device and their values.

        Returns:
            DeviceUpdate[Outputs]:
                The produced update event.
        """
        print("HELLLL")
        new_x, new_y, new_z, new_omega = (
            inputs["x"],
            inputs["y"],
            inputs["z"],
            inputs["omega"],
        )

        print("HELLLL")
        if new_x != self.x or new_y != self.y or new_z != self.y:
            self.reset_waveform_position(new_x, new_y, new_z, new_omega)

            self.x, self.y, self.z, self.omega = new_x, new_y, new_z, new_omega

        print("HELLLL")
        self.set_waveform_based_on_omega()

        print("HELLLL")
        return DeviceUpdate(
            OAVDeviceMXSC.Outputs(), SimTime(time + self.callback_period)
        )

    def get_omega(self):
        """Getter for pv."""
        return self.omega

    def get_high_limit_travel(self):
        """Getter for pv."""
        return self.high_limit_travel

    def get_low_limit_travel(self):
        """Getter for pv."""
        return self.high_limit_travel

    def get_top(self) -> np.ndarray:
        """Getter for pv."""
        return self.top

    def get_bottom(self) -> np.ndarray:
        """Getter for pv."""
        return self.bottom

    def get_tip_x(self) -> int:
        """Getter for pv."""
        return self.tip_x

    def get_tip_y(self) -> int:
        """Getter for pv."""
        return self.tip_y


class OAVEpicsAdapterMXSC(EpicsAdapter):
    """
    Epics adapter for handling edge detection PVs.
    """

    device: OAVDeviceMXSC

    # Put all the PVs on EPICS
    def on_db_load(self) -> None:
        """Epics adapter for reading device values as a PV through channel access."""
        self.link_input_on_interrupt(
            builder.WaveformOut("MXSC:Top", self.device.top), self.device.get_top
        )
        self.link_input_on_interrupt(
            builder.WaveformOut("MXSC:Bottom", self.device.bottom),
            self.device.get_bottom,
        )
        self.link_input_on_interrupt(builder.aOut("MXSC:TipX"), self.device.get_tip_x)
        self.link_input_on_interrupt(builder.aOut("MXSC:TipY"), self.device.get_tip_y)


class OAVEpicsAdapter(EpicsAdapter):
    """Epics adapter for reading all Attributes as a PV through channel access."""

    device: OAVDevice

    # Put all the PVs on EPICS
    def on_db_load(self) -> None:
        """Epics adapter for reading device values as a PV through channel access."""
        pass


@dataclass
class OAV_DEVICE_DEFAULT(ComponentConfig):
    """Parent class for various OAV devices."""

    name: str
    db_file: str
    ioc_name: str

    def __call__(self) -> Component:
        """Set up simulation."""
        return DeviceSimulation(
            name=self.name,
            device=OAVDevice(),
            adapters=[
                OAVEpicsAdapter(self.db_file, self.ioc_name),
            ],
        )


@dataclass
class OAV_DI_OAV(ComponentConfig):
    """To hold DI-OAV PVs."""

    name: str
    db_file: str
    ioc_name: str

    def __call__(self) -> Component:
        """Set up simulation."""
        return DeviceSimulation(
            name=self.name,
            device=OAVDeviceMXSC(),
            adapters=[
                OAVEpicsAdapterMXSC(self.db_file, self.ioc_name),
            ],
        )
