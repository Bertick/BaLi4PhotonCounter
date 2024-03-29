"""
Module implements a wrapper class for the hardware library. Errors from c-style library are converted to Python
exceptions, similarly c-style variables are converted to Python variables as needed.
"""
from ctypes import byref, c_uint32, c_uint16, c_uint8
import os.path

import platform

# I wrote the software mostly under Linux, but the hardware library only works on Windows. So i made a 'fakelib' module
# that simulates the hardware for debugging purposes.
OS = platform.system()
if OS == 'Linux':
    import PhotonCounter.fakelib as libhandle
elif OS == 'Windows':
    from ctypes import windll
    print(os.path.join(os.path.realpath('..'), 'C8855-01api.dll'))
    libhandle = windll.LoadLibrary(os.path.join(os.path.realpath('.'), 'C8855-01api.dll'))
else:
    raise RuntimeError(f"Wrong OS, got {OS}")

USB_TIMEOUT = 2

# Hamamatsu gate times
# key -> (ctype value, Gate number, seconds)
# ctype value is set to hardware during setup
# Gate number decides the dimensions of the data array populated by read_data() function
# seconds is the floating point value of the gate_time (used in calcs later)
GATE_TIMES = {
    '50US':  (c_uint8(2), 500,  50e-6),
    '100US': (c_uint8(3), 500, 100e-6),
    '200US': (c_uint8(4), 500, 200e-6),
    '500US': (c_uint8(5), 500, 500e-6),
    '1MS':   (c_uint8(6), 200,   1e-3),    # manually edited (original Gates = 500)
    '2MS':   (c_uint8(7), 100,   2e-3),    # manually edited (original Gates = 250)
    '5MS':     (c_uint8(8),  40,   5e-3),  # manually edited (original Gates = 100)
    '10MS':    (c_uint8(9),  20,  10e-3),  # manually edited (original Gates = 50)
    '20MS':    (c_uint8(10), 10,  20e-3),  # manually edited (original Gates = 25)
    '50MS':    (c_uint8(11), 10,  50e-3),
    '100MS':   (c_uint8(12),  5, 100e-3),
    '200MS':   (c_uint8(13),  5, 200e-3),
    '500MS':   (c_uint8(14),  5, 500e-3),
    # '1S':    (c_uint8(15),  5,   1.0),
    # '2S':    (c_uint8(16),  5,   2.0),
    # '5S':    (c_uint8(17),  5,   5.0),
    # '10S':   (c_uint8(18),  5,  10.0)
}

SOFTWARE_TRIGGER = c_uint8(0)
EXTERNAL_TRIGGER = c_uint8(1)

SINGLE_TRANSFER = c_uint8(1)
BLOCK_TRANSFER = c_uint8(2)

PMT_POWER_OFF = c_uint8(0)
PMT_POWER_ON = c_uint8(1)
PMT_POWER_CHECK = c_uint8(2)

MAX_HANDLES = 16


def _is_good_handle(handle):
    """
    Checks if the 'handle' variable represents a good handle pointer for the Hardware
    (it's supposed to be a positive integer)
    """
    if handle is None or handle <= 0:
        return False
    return True


# def minit(handles):
#     """
#     Attempts to open a list of handles and returns multiple Hamamatsu objects. used for multi-hardware support
#     (NOT IMPLEMENTED)
#     """
#     objs = []
#     for hh in handles:
#         obj = Hamamatsu(hh)
#         obj.read_id()
#         print(f'Detected hardware with uid = {obj.uid}')
#         objs.append(obj)
#     return objs


def _open():
    """
    Protected function for opening a single Hardware connection.
    """
    handle = libhandle.C8855Open()
    if not _is_good_handle(handle):
        raise ValueError(f"No Hardware detected, got handle {handle}.")
    return handle


class Hamamatsu:
    """
    Class represents a single counting unit. Hardware connection is made through the factory method .open()
    """
    def __init__(self, *, handle: int = 0):
        # universal ID
        self.uid = -1
        self.hhandle = handle
        self.is_powered = False
        self.is_counting = False

        self._gate_time = ''
        self.gates = -1

    #######################
    # CLIENT SIDE FACTORY #
    #######################
    @classmethod
    def open(cls):
        """
        Factory method for initializing a single counting unit.
        :return: Hamamatsu object
        """
        # todo: as long as multiple hardware support is not in place, this should behave as a singleton.
        handle = _open()
        obj = cls(handle=handle)
        obj.read_id()
        return obj

    ####################
    # CLIENT INTERFACE #
    ####################
    def close(self):
        if libhandle.C8855Close(self.hhandle) == 0:
            raise RuntimeError(f'Could not close handle {self.hhandle}')

    def reset(self):
        if libhandle.C8855Reset(self.hhandle) == 0:
            raise RuntimeError(f'Could not reset handle {self.hhandle}')

    def count_start(self):
        if libhandle.C8855CountStart(self.hhandle, SOFTWARE_TRIGGER) == 0:
            raise RuntimeError(f'Could not start count process for handle {self.hhandle}')
        self.is_counting = True

    def count_stop(self):
        if libhandle.C8855CountStop(self.hhandle) == 0:
            raise RuntimeError(f'Could not stop count process for handle {self.hhandle}')
        self.is_counting = False

    def setup(self, mode: int):
        # transfer mode (generally we use BLOCK_TRASFER)
        mode_c = SINGLE_TRANSFER if mode == 0 else BLOCK_TRANSFER
        # gate number using ctype
        n_gates_c = c_uint16(self.gates)
        # gate time hardware code
        gtime_c = GATE_TIMES[self.gate_time][0]
        #
        if libhandle.C8855Setup(self.hhandle, gtime_c, mode_c, n_gates_c) == 0:
            raise RuntimeError(f'Could not setup handle {self.hhandle}')

    def set_power(self, status: bool):
        pow_mode = PMT_POWER_ON if status else PMT_POWER_OFF
        if libhandle.C8855SetPmtPower(self.hhandle, pow_mode) == 0:
            raise RuntimeError(f'Could not set power for handle {self.hhandle}')
        self.is_powered = status

    def read_data(self):
        data_type = c_uint32 * self.gates
        data = data_type()
        result = c_uint8()
        if libhandle.C8855ReadData(self.hhandle, byref(data), byref(result)) == 0:
            raise RuntimeError(f'Could not read data from handle {self.hhandle}')
        if result.value < 0:
            raise RuntimeError(f'Error during data readout (handle {self.hhandle})')
        # the 'data' array contains the counts per gate (each represents photon counts after 'gate time' seconds)
        # return the whole array and plot it

        # the '[:]' takes all elements of array, this is to ensure we return a copy of the array and not the pointer
        # it. Since this array it's going to be overridden next data acquisition.
        return data[:]

    def read_id(self):
        uid = c_uint8()
        if not libhandle.C8855ReadId(self.hhandle, byref(uid)):
            raise RuntimeError(f'Could not read ID from handle {self.hhandle}')
        self.uid = uid.value

    @property
    def gate_time(self):
        return self._gate_time

    @gate_time.setter
    def gate_time(self, value: str):
        self._gate_time = value
        self.gates = GATE_TIMES[value][1]

    #############
    # INTERNALS #
    #############
    def get_gatetime_data(self):
        return GATE_TIMES[self._gate_time]

    # def _compute_iterations(self):
    #     gates = TRANS[self.gate_time]
    #     gates = min(gates, DEFAULT_MEASUREMENT_POINTS)
    #     r, iq = DEFAULT_MEASUREMENT_POINTS % gates, DEFAULT_MEASUREMENT_POINTS // gates
    #
    #     iterations = iq
    #     if not r:
    #         iterations += 1
    #     self.iterations = iterations
    #     self.gates = gates

