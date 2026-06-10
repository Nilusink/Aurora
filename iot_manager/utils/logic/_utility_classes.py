"""
_utility_classes.py
25. January 2024

defines a few useful classes

Author:
Nilusink, melektron
"""
import asyncio
import inspect
import math as m
import typing as tp
from time import perf_counter


class BetterDict:
    """
    each element is also accessible with instance.element
    """
    def __init__(self, **initial) -> None:
        for key, value in initial.items():
            setattr(self, key, value)

    def __setitem__(self, key: str, value: tp.Any) -> None:
        setattr(self, key, value)

    def __getitem__(self, item: str) -> tp.Any:
        return self.__dict__[item]

    def __delitem__(self, key) -> None:
        delattr(self, key)


class SimpleLock:
    def __init__(self) -> None:
        self.__locked_by: str = ...

    def acquire(
        self,
        timeout: float = 0
    ) -> bool:
        """
        :param timeout: timeout in seconds
        """
        start = perf_counter()

        curframe = inspect.currentframe()
        called_by = inspect.getouterframes(curframe, 2)[1][3]

        while perf_counter() - start > timeout or timeout == 0:
            if self.__locked_by is ...:
                self.__locked_by = called_by
                return True

        return False

    def release(self) -> None:
        """
        release a lock (only works from same function)
        """
        curframe = inspect.currentframe()
        called_by = inspect.getouterframes(curframe, 2)[1][3]

        if called_by != self.__locked_by:
            raise NameError("Lock can't be released from different function!")

        self.__locked_by = ...

