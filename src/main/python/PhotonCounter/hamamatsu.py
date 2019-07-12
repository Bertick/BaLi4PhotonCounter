import os.path
from ctypes import windll, byref, c_long, c_byte
subfolders = ['src', 'main', 'python', 'Libs', 'C8855-01api.dll']
libpath = os.path.join(os.path.realpath('.'), *subfolders)
libhandle = windll.LoadLibrary(libpath)

USB_TIMEOUT = 1

# Hamamatsu gate times
GATE_TIMES = {
    '50US': b'0x02h',
    '100US': b'0x03h',
    '200US': b'0x04h',
    '500US': b'0x05h',
    '1MS': b'0x06h',
    '2MS': b'0x07h',
    '5MS': b'0x08h',
    '10MS': b'0x09h',
    '20MS': b'0x0Ah',
    '50MS': b'0x0Bh',
    '100MS': b'0x0Ch',
    '200MS': b'0x0Dh',
    '500MS': b'0x0Eh',
    '1S': b'0x0Fh',
    '2S': b'0x10h',
    '5S': b'0x11h',
    '10S': b'0x12h'
}

SOFTWARE_TRIGGER = 0
EXTERNAL_TRIGGER = 1

SINGLE_TRANSFER = 1
BLOCK_TRANSFER = 2

PMT_POWER_OFF = 0
PMT_POWER_ON = 1
PMT_POWER_CHECK = 2


class Hamamatsu:
    def __init__(self):
        self._hhandle = None

    def hardware_init(self):
        self._hhandle = libhandle.C8855Open()
        # todo: how do we check if this is a good handle? manual says nothing
        self.reset()

    def _check_handle(self):
        if self._hhandle is None:
            raise ValueError('Hardware is not yet initialized')

    def reset(self):
        self._check_handle()
        if libhandle.C8855Reset(self._hhandle) == 0:
            raise RuntimeError('Could not reset')

    def close(self):
        self._check_handle()
        if libhandle.C8855Close(self._hhandle) == 0:
            raise RuntimeError('Could not close')

    def count_start(self):
        self._check_handle()
        if libhandle.C8855CountStart(self._hhandle, SOFTWARE_TRIGGER) == 0:
            raise RuntimeError('Could not start count process')

    def count_stop(self):
        self._check_handle()
        if libhandle.C8855CountStop(self._hhandle) == 0:
            raise RuntimeError('Could not stop count process')

    def setup(self, gtime: str, mode: int, n_gates: int):
        self._check_handle()
        if libhandle.C8855Setup(self._hhandle, GATE_TIMES[gtime], mode, n_gates) == 0:
            raise RuntimeError('Could not setup the hardware')

    def read_data(self):
        self._check_handle()
        # todo: we need better understanding of the different transfer mode
        data_type = 200 * c_long
        data = data_type()
        result = c_byte()
        if libhandle.C8855ReadData(self._hhandle, byref(data), byref(result)) == 0:
            raise RuntimeError('Could not read data')
        # todo: check if 'result' is not an error
        return data

    def set_power(self, status: bool):
        self._check_handle()
        pow_mode = PMT_POWER_ON if status else PMT_POWER_OFF
        if libhandle.C8855SetPmtPower(self._hhandle, pow_mode) == 0:
            raise RuntimeError('Could not set power')

    @staticmethod
    def set_timeout():
        if libhandle.C8855TimeOut(USB_TIMEOUT * 1000) == 0:
            raise RuntimeError('Could not set timeout')








