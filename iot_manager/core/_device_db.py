"""
Device database interface.

| ``Path``: iot_manager/core/_device_db.py
| ``Project``: IOTManager
| ``Created``: 10.06.2026
| ``Authors``: Nilusink
"""

import ipaddress
import sqlite3
import typing as tp
from os import PathLike
from types import EllipsisType

from ._datatypes import EndpointType, IOTDevice

DEFAULT_TABLES: tp.Final[list[str]] = [
    """CREATE TABLE IF NOT EXISTS device_data
(
    id   integer not null
        constraint table_name_pk
            primary key autoincrement,
    ip   integer not null,
    port integer not null
)""",
    """CREATE TABLE IF NOT EXISTS endpoints
(
    eid  integer not null
        constraint eid_pk
            primary key autoincrement,
    name text    not null,
    type integer not null,
    did  integer not null
        constraint endpoints_device_data_id_fk
            references device_data
)""",
]


class DeviceDB:
    """
    Device database interface.

    :cvar _default_path: default database path.

    :ivar _conn: sqlite3 connection.
    """

    # region ClassVars
    _default_path: tp.ClassVar[str] = "./devices.db"
    # endregion

    # region InstanceVars
    _conn: sqlite3.Connection
    # endregion

    def __init__(self, path: PathLike | EllipsisType = ...) -> None:
        if isinstance(path, EllipsisType):
            path_ = self._default_path

        else:
            path_ = path

        self._conn = sqlite3.connect(path_)

    def __check_create(self) -> None:
        """Check if all tables exist, if not, create them."""
        cursor = self._conn.cursor()

        # iterate default tables
        for table in DEFAULT_TABLES:
            cursor.execute(table)

        # apply changes
        self._conn.commit()
        cursor.close()

    def get_devices(self) -> list[IOTDevice]:
        """
        Get all devices.

        :return: list of all registered device.
        """
        cursor = self._conn.cursor()

        # get all devices
        cursor.execute("SELECT id, ip, port FROM device_data;")

        # create devices
        out = []
        for device in cursor.fetchall():
            # get endpoints and convert to device
            out.append(
                IOTDevice(
                    id=device[0],
                    address=(ipaddress.IPv4Address(device[1]), device[2]),
                    endpoints=self.get_endpoints(device[0]),
                )
            )

        cursor.close()
        return out

    def get_device(
        self,
        device_id: int | None = None,
        device_ip: ipaddress.IPv4Address | None = None,
    ) -> IOTDevice:
        """
        Get a single device.

        :param device_id: id of device (one must be given).
        :param device_ip: ip of device (one must be given).
        :return: device data.
        :raises KeyError: if device not found.
        :raises RuntimeError: if neither IP nor ID are given
        """
        if (device_ip is None) and (device_id is None):
            msg = f"Either device IP or ID must be given! ({device_id=}, {device_ip=})"
            raise RuntimeError(msg)

        if device_ip is None:
            ip_ = -1

        else:
            ip_ = int(device_ip)

        cursor = self._conn.cursor()

        # get device data
        by_id = device_id is not None
        cursor.execute(
            "SELECT id, ip, port FROM device_data "
            f"where {'id' if by_id else 'ip'} = ?",
            (device_id if by_id else ip_,),  # type: ignore[trust]
        )

        # fetch data
        data = cursor.fetchone()
        cursor.close()

        if not data:
            msg = f"Invalid device ID={device_id}"
            raise KeyError(msg)

        # convert to device
        return IOTDevice(
            id=data[0],
            address=(ipaddress.IPv4Address(data[1]), data[2]),
            endpoints=self.get_endpoints(data[0]),
        )

    def get_address(self, device_id: int) -> tuple[ipaddress.IPv4Address, int]:
        """
        Get a device's address.

        :param device_id: id of desired device
        :return: IP, port
        :raises KeyError: if device not found.
        """
        cursor = self._conn.cursor()

        # get data
        cursor.execute(
            "SELECT ip, port FROM device_data WHERE id = ?;",
            (device_id,),
        )
        data = cursor.fetchone()
        cursor.close()

        if not data:
            msg = f"Invalid device ID={device_id}"
            raise KeyError(msg)

        return ipaddress.IPv4Address(data[0]), data[1]

    def get_endpoints(self, device_id: int) -> list[tuple[str, EndpointType]]:
        """
        Get all endpoints for a device.

        :param device_id: id of device.
        :return: list of endpoints.
        """
        cursor = self._conn.cursor()

        # query search
        cursor.execute(
            "SELECT name, type from endpoints where did = ?",
            (device_id,),
        )

        # get results
        endpoints = cursor.fetchall()
        cursor.close()

        return [(e[0], EndpointType(e[1])) for e in endpoints]

    def get_ip_addresses(self) -> list[ipaddress.IPv4Address]:
        """
        Get all reserved IP addresses.

        :return: list of reserved IP addresses.
        """
        cursor = self._conn.cursor()

        # query ip addresses
        cursor.execute("SELECT ip FROM device_data;")

        # get data
        data = cursor.fetchall()
        cursor.close()

        # convert to IPv4 addresses
        return [ipaddress.IPv4Address(e[0]) for e in data]

    def register_device(
        self,
        ip: ipaddress.IPv4Address,
        port: int,
        endpoints: list[tuple[str, EndpointType]],
        device_id: int | None = None,
    ) -> int:
        """
        Register a new device.

        :param device_id: id of new device, if none, it will auto-increment
        :param ip: ip address of new device
        :param port: port of new device
        :param endpoints: endpoints of new device
        :return: id of new device, else: -1: id conflict, -2: ip conflict,
            -3: create failure
        """
        cursor = self._conn.cursor()

        # check if device already exists
        cursor.execute(
            "SELECT * FROM device_data WHERE id = ?",
            (device_id,),
        )
        if cursor.fetchone() is not None:
            return -1

        # check if IP already exists
        ip_: int = int(ip)
        cursor.execute(
            "SELECT id FROM device_data WHERE ip = ?",
            (ip_,),
        )
        if cursor.fetchone() is not None:
            return -2

        # device doesn't exist, create it
        if device_id is None:
            cursor.execute(
                "INSERT INTO device_data (ip, port) VALUES (?, ?)",
                (ip_, port),
            )
            self._conn.commit()

            # get id of new device
            did: int = cursor.lastrowid or -3

            if did < 0:
                cursor.close()
                return did

        else:
            cursor.execute(
                "INSERT INTO device_data (id, ip, port) VALUES (?, ?, ?)",
                (device_id, ip_, port),
            )
            did: int = device_id

        # create endpoints
        for endpoint in endpoints:
            cursor.execute(
                "INSERT INTO endpoints (did, name, type) VALUES (?, ?, ?)",
                (did, endpoint[0], endpoint[1].value),
            )

        # commit changes
        self._conn.commit()
        cursor.close()

        return did


if __name__ == "__main__":
    db = DeviceDB()
    print(db.get_device(1))
    # print(
    #     db.register_device(
    #         "192.168.68.15",
    #         80,
    #         [("weather", EndpointType.GET), ("blink", EndpointType.POST)],
    #     )
    # )
