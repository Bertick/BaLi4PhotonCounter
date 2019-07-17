import os.path
import threading as th
from ctypes import windll, byref, c_int32, c_uint32, c_uint16, c_uint8
from functools import wraps

libhandle = windll.LoadLibrary('C8855-01api.dll')

USB_TIMEOUT = 2

# Hamamatsu gate times
GATE_TIMES = {
    # '50US': c_uint8(2),
    # '100US': c_uint8(3),
    # '200US': c_uint8(4),
    # '500US': c_uint8(5),
    # '1MS': c_uint8(6),
    # '2MS': c_uint8(7),
    '5MS': c_uint8(8),
    '10MS': c_uint8(9),
    '20MS': c_uint8(10),
    '50MS': c_uint8(11),
    '100MS': c_uint8(12),
    '200MS': c_uint8(13),
    '500MS': c_uint8(14),
    # '1S': c_uint8(15),
    # '2S': c_uint8(16),
    # '5S': c_uint8(17),
    # '10S': c_uint8(18)
}

# no idea what it means but it was like this in their example
TRANS = {
    '50US': 500,
    '100US': 500,
    '200US': 500,
    '500US': 500,
    '1MS': 500,
    '2MS': 250,
    '5MS': 100,
    '10MS': 50,
    '20MS': 25,
    '50MS': 10,
    '100MS': 5,
    '200MS': 5,
    '500MS': 5,
    '1S': 5,
    '2S': 5,
    '5S': 5,
    '10S': 5
}

SOFTWARE_TRIGGER = c_uint8(0)
EXTERNAL_TRIGGER = c_uint8(1)

SINGLE_TRANSFER = c_uint8(1)
BLOCK_TRANSFER = c_uint8(2)

PMT_POWER_OFF = c_uint8(0)
PMT_POWER_ON = c_uint8(1)
PMT_POWER_CHECK = c_uint8(2)

# HANDLES
MAX_HANDLES = 16
u_handle = None
handles = []


def threaded(f):
    @wraps(f)
    def wrapper(*args):
        _executor = th.Thread(name='executor', target=f, args=args, daemon=True)
        _executor.start()

        # wait USB_TIMEOUT for the executor to finish
        _executor.join(USB_TIMEOUT)

        if _executor.is_alive():
            # timeout occurred
            _executor._delete()
            raise TimeoutError()
    return wrapper


@threaded
def sopen():
    global u_handle
    u_handle = libhandle.C8855Open()


@threaded
def mopen(nunits):
    global handles
    handles = [c_int32() for _ in range(MAX_HANDLES)]
    hh_refs = [byref(hh) for hh in handles]
    libhandle.C8855MOpen(nunits, *hh_refs)


def is_good_handle(handle):
    if handle is None or handle.value <= 0:
        return False
    return True


def minit(nunits):
    mopen(nunits)
    hama_objs = []

    global handles
    for hh in handles:
        if is_good_handle(hh):
            obj = Hamamatsu(hh)
            obj.read_id()
            print(f'Detected hardware with uid = {obj.uid}')
            hama_objs.append(obj)
    return hama_objs


class Hamamatsu:
    def __init__(self, handle: c_int32):
        self.uid = -1
        self.hhandle = handle
        self.is_powered = False
        self.is_counting = False

        self.iterations = -1
        self.gates = -1

    def reset(self):
        if libhandle.C8855Reset(self.hhandle) == 0:
            raise RuntimeError('Could not reset')

    def close(self):
        if libhandle.C8855Close(self.hhandle) == 0:
            raise RuntimeError('Could not close')

    def count_start(self):
        if libhandle.C8855CountStart(self.hhandle, SOFTWARE_TRIGGER) == 0:
            raise RuntimeError('Could not start count process')
        self.is_counting = True

    def count_stop(self):
        if libhandle.C8855CountStop(self.hhandle) == 0:
            raise RuntimeError('Could not stop count process')
        self.is_counting = False

    def setup(self, gtime: str, mode: int, n_gates: int):
        mode_c = SINGLE_TRANSFER if mode == 0 else BLOCK_TRANSFER
        n_gates_c = c_uint16(n_gates)
        if libhandle.C8855Setup(self.hhandle, GATE_TIMES[gtime], mode_c, n_gates_c) == 0:
            raise RuntimeError('Could not setup the hardware')

    def read_data(self, gates):
        # todo: we need better understanding of the different transfer mode
        data_type = c_uint32 * gates
        data = data_type()
        result = c_uint8()
        if libhandle.C8855ReadData(self.hhandle, byref(data), byref(result)) == 0:
            raise RuntimeError('Could not read data')
        if result.value < 0:
            raise RuntimeError('Error during data readout')
        return list(data)

    def set_power(self, status: bool):
        pow_mode = PMT_POWER_ON if status else PMT_POWER_OFF
        if libhandle.C8855SetPmtPower(self.hhandle, pow_mode) == 0:
            raise RuntimeError('Could not set power')
        self.is_powered = status

    @threaded
    def read_id(self):
        uid = c_uint8()
        if libhandle.C8855ReadId(self.hhandle, byref(uid)) == 0:
            raise RuntimeError('Could not read ID')
        self.uid = uid.value