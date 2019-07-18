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

MAX_HANDLES = 16


def thread_timeout(f):
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


def _is_good_handle(handle):
    if handle is None or handle.value <= 0:
        return False
    return True


class Hamamatsu:
    """Class represents a multitude of counting units"""
    def __init__(self):
        self.units = 0
        self.handles = []
        self.objs = []

    def _minit(self):
        for hh in self.handles:
            obj = _Hamamatsu(hh)
            obj.read_id()
            print(f'Detected hardware with uid = {obj.uid}')
            self.objs.append(obj)

    @thread_timeout
    def open(self):
        self.handles = [c_int32() for _ in range(MAX_HANDLES)]
        hh_refs = [byref(hh) for hh in self.handles]
        libhandle.C8855MOpen(MAX_HANDLES, *hh_refs)
        # filter the good handles
        self.handles = [h for h in self.handles if _is_good_handle(h)]
        self._minit()

    def reset(self):
        for obj in self.objs:
            obj.reset()

    def close(self):
        for obj in self.objs:
            obj.close()

    def count_start(self):
        for obj in self.objs:
            if obj.is_counting:
                continue
            obj.count_start()

    def count_stop(self):
        for obj in self.objs:
            if not obj.is_counting:
                continue
            obj.count_stop()

    def setup(self, gtime: str, mode: int, n_gates: int):
        for obj in self.objs:
            obj.setup(gtime, mode, n_gates)

    def read_data(self, gates):
        results = [[0.0]*gates for _ in self.objs]
        for i, obj in enumerate(self.objs):
            results[i] = obj.read_data(gates)
        return results

    def set_power(self, status: bool):
        for obj in self.objs:
            obj.set_power(status)


class _Hamamatsu:
    """Class represents a single counting unit"""
    def __init__(self, handle: c_int32):
        self.uid = -1
        self.hhandle = handle
        self.is_powered = False
        self.is_counting = False

        self.iterations = -1
        self.gates = -1

    def read_data(self, gates):
        data_type = c_uint32 * gates
        data = data_type()
        result = c_uint8()
        if libhandle.C8855ReadData(self.hhandle, byref(data), byref(result)) == 0:
            raise RuntimeError(f'Could not read data from handle {self.hhandle}')
        if result.value < 0:
            raise RuntimeError(f'Error during data readout (handle {self.hhandle})')
        return list(data)

    @thread_timeout
    def reset(self):
        if libhandle.C8855Reset(self.hhandle) == 0:
            raise RuntimeError(f'Could not reset handle {self.hhandle}')

    @thread_timeout
    def close(self):
        if libhandle.C8855Close(self.hhandle) == 0:
            raise RuntimeError(f'Could not close handle {self.hhandle}')

    @thread_timeout
    def count_start(self):
        if libhandle.C8855CountStart(self.hhandle, SOFTWARE_TRIGGER) == 0:
            raise RuntimeError(f'Could not start count process for handle {self.hhandle}')
        self.is_counting = True

    @thread_timeout
    def count_stop(self):
        if libhandle.C8855CountStop(self.hhandle) == 0:
            raise RuntimeError(f'Could not stop count process for handle {self.hhandle}')
        self.is_counting = False

    @thread_timeout
    def setup(self, gtime: str, mode: int, n_gates: int):
        mode_c = SINGLE_TRANSFER if mode == 0 else BLOCK_TRANSFER
        n_gates_c = c_uint16(n_gates)
        if libhandle.C8855Setup(self.hhandle, GATE_TIMES[gtime], mode_c, n_gates_c) == 0:
            raise RuntimeError(f'Could not setup handle {self.hhandle}')

    @thread_timeout
    def set_power(self, status: bool):
        pow_mode = PMT_POWER_ON if status else PMT_POWER_OFF
        if libhandle.C8855SetPmtPower(self.hhandle, pow_mode) == 0:
            raise RuntimeError(f'Could not set power for handle {self.hhandle}')
        self.is_powered = status

    @thread_timeout
    def read_id(self):
        uid = c_uint8()
        if libhandle.C8855ReadId(self.hhandle, byref(uid)) == 0:
            raise RuntimeError(f'Could not read ID from handle {self.hhandle}')
        self.uid = uid.value
