"""
_device_manager.py
08. November 2025

manages devices (surprise)

Author:
Nilusink
"""
import ipaddress
import typing as tp
from copy import copy
from ipaddress import IPv4Address

from ._datatypes import IOTDevice
from ._device_db import DeviceDB


class DeviceManager:
    """
    Manages all IOT devices.

    :ivar _db: device database instance
    """

    # region InstanceVars
    _db: DeviceDB
    # endregion

    def __init__(self):
        self._db = DeviceDB()

    def get_device(self, device_id: int) -> IOTDevice:
        """
        get device by its id

        :param device_id: target device id
        :return: iot device
        """
        return self._db.get_device(device_id=device_id)

    def get_devices(self) -> list[IOTDevice]:
        return self._db.get_devices()

    def get_address(self, device_id: int) -> tuple[IPv4Address, int]:
        """
        get a devices ip address (and port)

        :param device_id: target device id
        :return: (ip, port)
        """
        return self._db.get_address(device_id)

    def get_endpoints(self, device_id: int) -> tp.Iterable[tuple[str, str]]:
        """
        get all available endpoints of a device

        :param device_id: the device id
        :return: list of device endpoints [(endpoint, type), ...]
        """
        return [(e[0], e[1].name) for e in self._db.get_endpoints(device_id)]

    def find_by_ip(self, device_ip: str) -> int:
        """
        find a devices' id by its address

        :param device_ip:
        :return: -1 if not found
        """
        try:
            return self._db.get_device(device_ip=ipaddress.IPv4Address(device_ip)).id

        except KeyError:
            return -1
