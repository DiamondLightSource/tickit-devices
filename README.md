[![CI](https://github.com/DiamondLightSource/tickit-devices/actions/workflows/ci.yml/badge.svg)](https://github.com/DiamondLightSource/tickit-devices/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/DiamondLightSource/tickit-devices/branch/main/graph/badge.svg)](https://codecov.io/gh/DiamondLightSource/tickit-devices)
[![PyPI](https://img.shields.io/pypi/v/tickit-devices.svg)](https://pypi.org/project/tickit-devices)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

# tickit-devices

A collection of devices simulated using the `tickit <https://github.com/dls-controls/tickit>`_ framework.

Source          | <https://github.com/DiamondLightSource/tickit-devices>
:---:           | :---:
PyPI            | `pip install tickit-devices`
Docker          | `docker run ghcr.io/diamondlightsource/tickit-devices:latest`
Documentation   | <https://diamondlightsource.github.io/tickit-devices>
Releases        | <https://github.com/DiamondLightSource/tickit-devices/releases>

Safety Note
------------------------------------
These devices mimic real synchrotron devices and there is the potential for conflict with the real PVs if this is run on the same port as EPICS (5064).
If using this simulation to test software, set your ``EPICS_CA_SERVER_PORT`` environment variable to something nonstandard, e.g. 5065 or greater, so that your
tests are not confused between these and the real PVs. The `S03 <https://gitlab.diamond.ac.uk/controls/python3/s03_utils>`_ startup scripts manage the setting of
these ports automatically, so if you are using this as part of S03 you won't need to change anything. Do not run this simulation on a beamline controls machine!


Adding devices to the S03 simulation
------------------------------------
To add a device to s03, the config file required to run the tickit simulation should be present in ``s03_configs``.
Only changes pushed to main will be built into the ``tickit-devices`` image that s03 pulls from. Once the
image has been built with the new device and config, follow the instructions `here <https://gitlab.diamond.ac.uk/controls/python3/s03_utils>`_
to include it in S03.

<!-- README only content. Anything below this line won't be included in index.md -->

See https://diamondlightsource.github.io/tickit-devices for more detailed documentation.
