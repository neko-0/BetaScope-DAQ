import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

from pathlib import Path
from gpib_ctypes.gpib import _load_lib

_LIBGPIB_SO = "/usr/local/lib/libgpib.so"
try:
    _load_lib(_LIBGPIB_SO)
except FileNotFoundError:
    logger.critical(f"cannot find {_LIBGPIB_SO}")
    logger.critical("try to use envir setting LIBGPIB_SO")

    import os

    _load_lib(os.environ["LIBGPIB_SO"])

import pyvisa

from .base import Generator


class Agilent81110A(Generator):
    """
    Agilent 8110A/81104A waveform generator.
    """

    def __init__(self, board):
        self.board = board
        self.inst = None
        self.connect()

    def connect(self, *args, **kwargs):
        rm = pyvisa.ResourceManager("@py")
        self.inst = rm.open_resource(f"GPIB::{self.board}::INSTR")

    def initialize(self, *args, **kwargs):
        pass

    def reset(self, *args, **kwarg):
        pass

    def close(self, *args, **kwarg):
        pass

    def write(self, *args, **kwarg):
        return self.inst.write(*args, **kwargs)

    def query(self, *args, **kwarg):
        return self.inst.query(*args, **kwarg)

    def read(self, *args, **kwarg):
        return self.inst.read(*args, **kwarg)
