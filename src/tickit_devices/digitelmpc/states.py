from enum import IntEnum

class Status(IntEnum):
    """An enumerator for digitelMpc statuses"""
    STANDBY = 0
    STARTING = 1
    RUNNING = 2
    COOLDOWN = 3
    ERROR = 4

class Error(IntEnum):
    """An enumerator for digitelMpc Errors"""
    OK = 0
    TOO_MANY_CYCLES = 1
    HIGH_PRESSURE = 2
    HIGH_CURRENT = 3
    PUMP_POWER = 4
    SHORT_CIRCUIT = 5
    MALFUNCTION = 6
    LOW_VOLTAGE = 7
    ARC_DETECT = 8

class SpRelay(IntEnum):
    """An enumerator for digitelMpc SP relay mode"""
    ON = 0
    OFF = 1