tickit-devices
===============

|code_ci| |coverage| |license|

A collection of devices simulated using the `tickit <https://github.com/dls-controls/tickit>`_ framework.


Synchrotron
------------
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
