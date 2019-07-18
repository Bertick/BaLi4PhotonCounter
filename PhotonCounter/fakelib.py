
def C8855Reset(h):
    return 1


def C8855Close(h):
    return 1


def C8855CountStart(h, s):
    return 1


def C8855CountStop(h):
    return 1


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
