tickit-devices
===============

|code_ci| |coverage| |license|

A collection of devices simulated using the `tickit <https://github.com/dls-controls/tickit>`_ framework.


Adding devices to the S03 simulation
------------------------------------
To add a device to s03, the config file required to run the tickit simulation should be present in `s03_configs`.
Only changes pushed to main will be built into the `tickit-devices` image that s03 pulls from. Once the 
image has been built with the new device and config, follow the instructions `here <https://gitlab.diamond.ac.uk/controls/python3/s03_utils>`_
to include it in S03.


Devices
-------
Information about the current devices and their stage of developement.

Synchrotron
~~~~~~~~~~~
A device created for the `Artemis <https://github.com/DiamondLightSource/python-artemis>`_ project. This device currently just acts to provide
PV values and an IOC which Ophyd can connect with to run system tests.

This device is in its minimum working state. There is much room for improvement.

To do:
+++++++
- Add record logic to the devices so they are interconnected


.. |code_ci| image:: https://github.com/dls-controls/tickit-devices/workflows/Code%20CI/badge.svg?branch=main
    :target: https://github.com/dls-controls/tickit-devices/actions?query=workflow%3A%22Code+CI%22
    :alt: Code CI

.. |coverage| image:: https://codecov.io/gh/dls-controls/tickit-devices/branch/main/graph/badge.svg
    :target: https://codecov.io/gh/dls-controls/tickit-devices
    :alt: Test Coverage

.. |license| image:: https://img.shields.io/badge/License-Apache%202.0-blue.svg
    :target: https://opensource.org/licenses/Apache-2.0
    :alt: Apache License
