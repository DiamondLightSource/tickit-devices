tickit-devices
===============

|coverage| |license|

A collection of devices simulated using the `tickit <https://github.com/dls-controls/tickit>`_ framework.


Synchrotron
------------
A device created for the `Artemis <https://github.com/DiamondLightSource/python-artemis>`_ project. This device currently just acts to provide
PV values and an IOC which Ophyd can connect with to run system tests.

This device is in its minimum working state. There is much room for improvement.

To do:
+++++++
- Add record logic to the devices so they are interconnected



.. |coverage| image:: https://codecov.io/gh/dls-controls/tickit/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/dls-controls/tickit
    :alt: Test Coverage

.. |license| image:: https://img.shields.io/badge/License-Apache%202.0-blue.svg
    :target: https://opensource.org/licenses/Apache-2.0
    :alt: Apache License
