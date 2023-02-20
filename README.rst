tickit-devices
===============

|code_ci| |docs_ci| |coverage| |pypi_version| |license|

A collection of devices simulated using the `tickit <https://github.com/dls-controls/tickit>`_ framework.

============== ==============================================================
PyPI           ``pip install tickit-devices``
Source code    https://github.com/dls-controls/tickit-devices
Documentation  https://dls-controls.github.io/tickit-devices
Releases       https://github.com/dls-controls/tickit-devices/releases
============== ==============================================================


Adding devices to the S03 simulation
------------------------------------
To add a device to s03, the config file required to run the tickit simulation should be present in ``s03_configs``.
Only changes pushed to main will be built into the ``tickit-devices`` image that s03 pulls from. Once the 
image has been built with the new device and config, follow the instructions `here <https://gitlab.diamond.ac.uk/controls/python3/s03_utils>`_
to include it in S03.


.. |code_ci| image:: https://github.com/dls-controls/tickit-devices/workflows/Code%20CI/badge.svg?branch=main
    :target: https://github.com/dls-controls/tickit-devices/actions?query=workflow%3A%22Code+CI%22
    :alt: Code CI

.. |docs_ci| image:: https://github.com/dls-controls/tickit-devices/actions/workflows/docs.yml/badge.svg?branch=main
    :target: https://github.com/dls-controls/tickit-devices/actions/workflows/docs.yml
    :alt: Docs CI

.. |coverage| image:: https://codecov.io/gh/dls-controls/tickit-devices/branch/main/graph/badge.svg
    :target: https://codecov.io/gh/dls-controls/tickit-devices
    :alt: Test Coverage

.. |pypi_version| image:: https://img.shields.io/pypi/v/python3-pip-skeleton.svg
    :target: https://pypi.org/project/tickit-devices
    :alt: Latest PyPI version

.. |license| image:: https://img.shields.io/badge/License-Apache%202.0-blue.svg
    :target: https://opensource.org/licenses/Apache-2.0
    :alt: Apache License

..
    Anything below this line is used when viewing README.rst and will be replaced
    when included in index.rst

See https://dls-controls.github.io/tickit-devices for more detailed documentation.