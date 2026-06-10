# from time import sleep
import asyncio
import signal
import sys
from time import perf_counter

from icecream import ic

from iot_manager.core import DeviceBuffer, DeviceManager, HTTPServer, IOTDevice
from iot_manager.utils.debugging import DebugLevel, debugger

SIGNALS: list[signal.Signals]
if sys.platform == 'win32':
    SIGNALS = [signal.SIGINT, signal.SIGTERM]

else:
    SIGNALS = [signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGPIPE]


async def main() -> None:
    # debugging setup
    start = perf_counter()

    def time_since_start() -> str:
        """
        stylized time since game start
        gamestart being time since `mainloop` was called
        """
        t_ms = round(perf_counter() - start, 4)

        t1, t2 = str(t_ms).split(".")
        return f"{t1: >4}.{t2: <4} |> "

    ic.configureOutput(prefix=time_since_start)
    debugger.init(
        "./IOTManager.log",
        write_debug=True,
        debug_level=DebugLevel.log
    )

    # manager
    dev_man = DeviceManager()

    # buffer
    dev_buf = DeviceBuffer()

    # add device 0 and 1 to request buffer
    dev_buf.add_device(dev_man.get_device(0), 2)
    dev_buf.add_device(dev_man.get_device(1), 2)

    # http server
    server = HTTPServer(
        dev_buf,
        dev_man,
        ("127.0.0.1", 12345)
    )

    # cleanup
    def cleanup(*_, **__) -> None:
        """
        correctly stops the program
        """
        debugger.log("main: stopping program ...")
        dev_buf.shutdown()
        debugger.info("main: IOTManager stopped")

    # register cleanup function for OS interrupts
    for s in SIGNALS:
        signal.signal(s, cleanup)

    debugger.info("main: IOTManager started")

    try:
        await asyncio.gather(server.serve())

    except KeyboardInterrupt:
        cleanup()


if __name__ == '__main__':
    asyncio.run(main())
