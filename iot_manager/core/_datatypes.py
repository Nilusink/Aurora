"""
_device_buffer.py
07. November 2025

-----------------------

Author:
Nilusink
"""

import ipaddress
from dataclasses import dataclass
from enum import Enum


class EndpointType(Enum):
    """Specify endpoint type."""

    GET = 0
    POST = 1
    PUT = 2


@dataclass(frozen=True)
class IOTDevice:
    """IOT device info."""

    id: int
    address: tuple[ipaddress.IPv4Address, int]
    endpoints: list[tuple[str, EndpointType]]  # e.g. ["/weather", "/brightness"], ["/"]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "address": (str(self.address[0]), self.address[1]),
            "endpoints": [(e[0], e[1].name) for e in self.endpoints],
        }


if __name__ == "__main__":
    print(EndpointType.GET.name)
