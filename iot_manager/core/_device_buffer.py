"""
_device_buffer.py
07. November 2025

Periodically requests data from an IOT sensor (e.g. Environment sensor)
and acts as a "relay" so subscribers can request data from one central
host and to remove stress from small ics

Author:
Nilusink
"""

import time
import typing as tp
from types import EllipsisType
from concurrent.futures import Future, ThreadPoolExecutor

import requests

from ..utils.debugging import debugger  # , DebugLevel  # , run_with_debug
from ._datatypes import IOTDevice, EndpointType


class _DeviceParams(tp.TypedDict):
    device: IOTDevice
    interval: float
    last_update: float
    last_data: dict[str, dict | EllipsisType]


class DeviceBuffer:
    _clients: dict[int, _DeviceParams]
    _current_client_id = 0

    def __init__(
        self,
    ) -> None:
        debugger.trace("dev_buf: initializing...")

        # variable setup
        self._clients = {}
        self.__running = True

        # threading
        self._pool = ThreadPoolExecutor(max_workers=8)

        # start background threads
        self._pool.submit(self._device_requester)

        debugger.log("dev_buf: initialized")

    def _device_requester(self) -> None:
        """
        background task, handles the device requests
        """
        debugger.trace("dev_buf: starting device requester")

        while self.__running:
            now = time.time()
            for did, device in self._clients.items():
                # check if device data needs to be updated
                if (now - device["last_update"]) > device["interval"]:
                    self._update_device(did, True)
                    device["last_update"] = time.time()

            time.sleep(0.1)

        debugger.trace("dev_buf: device requester stopped")

    # @run_with_debug(
    #     show_call=True,
    #     show_finish=True,
    #     reraise_errors=True,
    # )
    def _update_device(self, device_id: int, background: bool = True) -> None | Future:
        """
        update a devices data

        :param device_id: device to update
        :param background: starts thread if true
        """
        if background:
            return self._pool.submit(self._update_device, device_id, False)

        # request data from given address
        device = self._clients[device_id]
        dev: IOTDevice = device["device"]
        debugger.trace(
            f"dev_buf: updating device {device_id} at {device['device'].address}"
        )

        for endpoint, endpoint_type in dev.endpoints:
            # only request GET endpoints
            if endpoint_type != EndpointType.GET:
                continue
            
            debugger.trace(
                f"dev_buf: requesting http://{device['device'].address[0]}:"
                f"{device['device'].address[1]}/{endpoint}"
            )
            # request single endpoint and save to buffer
            try:
                data = requests.get(
                    f"http://{device['device'].address[0]}:"
                    f"{device['device'].address[1]}/{endpoint}",
                    timeout=min(device["interval"] / 2, 5),
                ).json()

            except (
                TimeoutError,
                requests.ReadTimeout,
                requests.ConnectTimeout,
                requests.ConnectionError,
            ):
                debugger.log(
                    f"dev_buf: failed to get data form {device['device'].address}"
                )
                continue

            device["last_data"][endpoint] = data

            debugger.trace(
                f'dev_buf: updated device {device_id} at "{endpoint}": {data}'
            )

        return None

    def add_device(self, device: IOTDevice, interval_s: float) -> int:
        """
        add an IOT device to the request list

        :param device: IOT device to add
        :param interval_s: interval in seconds between device requests
        :returns: client id
        """
        cid = device.id

        debugger.log(f"dev_buf: adding device {cid} at {device.address}")

        self._clients[cid] = {
            "device": device,
            "interval": interval_s,
            "last_update": 0,
            "last_data": {ep[0]: ... for ep in device.endpoints},
        }

        return cid

    def remove_device(self, device_id: int) -> bool:
        """
        remove an IOT device from the request list

        :param device_id: device to remove
        :return: success
        """
        debugger.log(f"dev_buf: removing device {device_id}")
        if device_id in self._clients:
            self._clients.pop(device_id)
            return True

        return False

    def get_device_data(self, device_id: int, endpoint: str) -> dict | int:
        """
        return the data of the given device and endpoint
        """
        if endpoint not in self._clients[device_id]["last_data"]:
            return -1

        return self._clients[device_id]["last_data"][endpoint]

    def shutdown(self) -> None:
        debugger.trace("dev_buf: shutdown called")

        if not self.__running:
            debugger.trace("dev_buf: already shutdown...")
            return

        # shutdown threads
        self.__running = False

        debugger.trace("dev_buf: waiting for threads ...")
        self._pool.shutdown(wait=True)

        debugger.log("dev_buf: shutdown")

    def __del__(self):
        debugger.trace("dev_buf: __del__ called")
        self.shutdown()
