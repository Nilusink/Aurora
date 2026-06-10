"""
_debugger.py
26. November 2024

Debugs stuff (fancy, right?)

Author:
Nilusink
"""
from enum import IntEnum
from os import PathLike

from icecream import ic

from ._console_colors import CC, get_fg_color
from ._utils import print_ic_style


class DebugLevel(IntEnum):
    error = 0
    warning = 1
    info = 2
    log = 3
    trace = 4


class _Debugger:
    _debug_colors: dict[str, str] = {
        "error": CC.fg.RED,
        "warning": CC.fg.YELLOW,
        "info": CC.bfg.CYAN,
        "log": CC.fg.WHITE,
        "trace": get_fg_color(240)
    }

    def __init__(self):
        self._log_file = ...
        self._print_debug = ...
        self._write_debug = ...
        self._debug_level = ...

        # # fancy stuff
        # for debug_level in self._debug_colors:
        #     ic(debug_level)
        #
        #     def tmp(self, *args):
        #         """
        #         level: {debug_level}
        #         """
        #         print(args)
        #         ic(self._debug_level, getattr(DebugLevel, debug_level), self._debug_level >= getattr(DebugLevel, debug_level))
        #         if self._debug_level >= getattr(DebugLevel, debug_level):
        #             self._write(*args, color=self._debug_colors[debug_level])
        #
        #     setattr(
        #         _Debugger,
        #         debug_level,
        #         types.MethodType(tmp, self)
        #     )

    def init(
            self,
            log_file: PathLike,
            print_debug: bool = True,
            write_debug: bool = True,
            debug_level: DebugLevel = DebugLevel.warning,
    ) -> None:
        self._log_file = log_file
        self._print_debug = print_debug
        self._write_debug = write_debug
        self._debug_level = debug_level

    @property
    def debug_level(self) -> DebugLevel:
        return self._debug_level

    def trace(self, *args) -> None:
        """
        level: trace
        """
        if self._debug_level >= DebugLevel.trace:
            self._write(*args, color=self._debug_colors["trace"])

    def info(self, *args) -> None:
        """
        level: info
        """
        if self._debug_level >= DebugLevel.info:
            self._write(*args, color=self._debug_colors["info"])

    def log(self, *args) -> None:
        """
        level: log
        """
        if self._debug_level >= DebugLevel.log:
            self._write(*args, color=self._debug_colors["log"])

    def warning(self, *args) -> None:
        """
        level: warning
        """
        if self._debug_level >= DebugLevel.warning:
            self._write(*args, color=self._debug_colors["warning"])

    def error(self, *args) -> None:
        """
        level: error
        """
        if self._debug_level >= DebugLevel.error:
            self._write(*args, color=self._debug_colors["error"])

    def _write(self, *args, color: str = CC.ctrl.ENDC) -> None:
        """
        actually writes / prints
        """
        prefix = ic.prefix()
        string_out = ""

        for arg in args:
            if isinstance(arg, str):
                string_out += arg

            elif hasattr(arg, "__repr__"):
                string_out += arg.__repr__()

            else:
                string_out += str(arg)

        # print to terminal
        if self._print_debug:
            print_ic_style(color, string_out, CC.ctrl.ENDC)

        # write to file
        if self._write_debug:
            with open(self._log_file, "a") as out:
                out.write(prefix + string_out + "\n")


debugger = _Debugger()
