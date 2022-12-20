"""smargon_motor_fetcher.py, for passing the smargon angle into oav_edge_detection.py.

oav_edge_detection.py requires the omega angle of the S03 motor to set the
current waveform based on. We can't pass this in from S03, so this temporary
solution will create a device which monitors BL03S-MO-SGON-01:[X, Y, Z, OMEGA]
for changes and outputs them to the edge detection tickit device.
"""

import re
import subprocess
from dataclasses import dataclass
from typing import IO, Tuple

from tickit.adapters.epicsadapter import EpicsAdapter
from tickit.core.components.component import Component, ComponentConfig
from tickit.core.components.device_simulation import DeviceSimulation
from tickit.core.device import Device, DeviceUpdate
from tickit.core.typedefs import SimTime
from tickit.utils.compat.typing_compat import TypedDict


class SmargonGetterDevice(Device):
    #: An empty typed mapping of device inputs
    Inputs: TypedDict = TypedDict("Inputs", {})
    #: A typed mapping containing the current output value
    Outputs: TypedDict = TypedDict(
        "Outputs", {"x": float, "y": float, "z": float, "omega": float}
    )

    def __init__(self):
        pass

    def get_xyz_omega_from_pvs(self) -> None:

        # Command to run to extract x,y,z,omega.
        command = (
            "caget BL03S-MO-SGON-01:X BL03S-MO-SGON-01:Y BL03S-MO-SGON-01:Z "
            "BL03S-MO-SGON-01:OMEGA"
        )

        # If two pods of S03 are running are running at the same time, the PV
        # will be extracted from the one on the machine you're running, however
        # a client exception can be shown (before or after the PV outputs). We
        # need to extract this error message out.

        # This is dead sketchy, hopefully motors will be implemented in
        # tickit soon enough.
        strip_start = (
            "CA.Client.Exception..............................................."
        )
        strip_end = ".................................................................."
        shell_output = subprocess.run(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        if shell_output is None:
            return self.x, self.y, self.z, self.omega

        assert shell_output.stdout is not None

        stripped = re.sub(
            strip_start + "(.*)" + strip_end, "", str(shell_output), flags=re.DOTALL
        )
        stripped_lines = stripped.split("\n")
        self.x = x, self.y = y, self.z = z, self.omega = (
            float(line.split()[1]) for line in stripped_lines[:-1]
        )

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

        self.x, self.y, self.z, self.omega = self.get_xyz_omega_from_pvs()
        return DeviceUpdate(
            SmargonGetterDevice.Outputs(x=self.x, y=self.y, z=self.z, omega=self.omega),
            SimTime(time + callback_period),
        )

    def get_x(self) -> float:
        """Getter for pv."""
        return self.x

    def get_y(self) -> float:
        """Getter for pv."""
        return self.x

    def get_z(self) -> float:
        """Getter for pv."""
        return self.x

    def get_omega(self) -> float:
        """Getter for pv."""
        return self.x

    def set_xyz_omega(self):
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.omega = 0.0


class SmargonGetterEpicsAdapter(EpicsAdapter):
    """
    Epics adapter for handling edge detection PVs.
    """

    device: SmargonGetterDevice

    # Put all the PVs on EPICS
    def on_db_load(self) -> None:
        pass


@dataclass
class SmargonGetter(ComponentConfig):
    """To hold DI-OAV PVs."""

    name: str
    db_file: str
    port: int
    ioc_name: str

    def __call__(self) -> Component:
        """Set up simulation."""
        return DeviceSimulation(
            name=self.name,
            device=SmargonGetterDevice(),
            adapters=[
                SmargonGetterEpicsAdapter(self.db_file, self.ioc_name),
            ],
        )
