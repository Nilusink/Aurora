"""
_http_server.py
08. November 2025

provides multiple endpoints making the manager available to the network

Author:
Nilusink
"""

from copy import copy
from http import HTTPStatus

import uvicorn
from fastapi import FastAPI, HTTPException
from icecream import ic

from ..utils.debugging import debugger
from ._device_buffer import DeviceBuffer
from ._device_manager import DeviceManager


class HTTPServer:
    def __init__(
        self,
        device_buffer: DeviceBuffer,
        device_manager: DeviceManager,
        address: tuple[str, int] = ("0.0.0.0", 12345),
    ) -> None:
        self._dev_buf = device_buffer
        self._dev_man = device_manager
        self._address = copy(address)

        self._app = FastAPI()

        # register endpoints
        self._setup_routes()

    def _setup_routes(self) -> None:
        # is alive
        @self._app.get("/")
        async def index() -> dict:
            """is alive check"""
            return {"hello": "world"}

        # device buffer
        @self._app.get("/device/{device_id}/data/{endpoint:path}")
        async def get_device_data(device_id: int, endpoint: str) -> dict:
            """
            forwards device requests

            :param device_id: device request id
            :param endpoint: normal device endpoint
            """
            endpoint = endpoint.strip().rstrip("/")
            debugger.trace(f'dev_buf: getting device {device_id}, "{endpoint}"')

            data = self._dev_buf.get_device_data(device_id, endpoint)

            if data == -1:
                debugger.info("dev_buf: invalid endpoint")
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                )

            elif data is ...:
                debugger.info("dev_buf: no data")
                raise HTTPException(
                    status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                )

            return data

        # device manager
        @self._app.get("/device/{device_id}")
        async def get_device(device_id: int) -> dict:
            try:
                device = self._dev_man.get_device(device_id)

            except KeyError:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                )

            return device.to_dict()

        @self._app.get("/device/{device_id}/address")
        async def get_address(device_id: int) -> dict:
            try:
                address = self._dev_man.get_address(device_id)

            except KeyError:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                )

            return {
                "ip": str(address[0]),
                "port": address[1],
            }

        @self._app.get("/device/{device_id}/endpoints")
        async def get_endpoints(device_id: int) -> dict:
            try:
                endpoints = self._dev_man.get_endpoints(device_id)

            except ValueError:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                )

            return {
                "endpoints": endpoints,
            }

        @self._app.get("/device/by_ip/{ip_address}")
        async def get_device_by_ip(ip_address: str) -> dict:
            did = self._dev_man.find_by_ip(ip_address)

            if did == -1:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                )

            device = self._dev_man.get_device(did)
            return device.to_dict()

    async def serve(self):
        """Run this buffer as its own FastAPI server."""
        config = uvicorn.Config(
            self._app,
            host=self._address[0],
            port=self._address[1],
            log_level="warning",
            # log_level={
            #     # DebugLevel.error: "error",
            #     # DebugLevel.warning: "warning",
            #     # DebugLevel.info: "info",
            #     # DebugLevel.log: "debug",
            #     # DebugLevel.trace: "trace"
            # }[debugger.debug_level]
        )
        server = uvicorn.Server(config)
        await server.serve()
