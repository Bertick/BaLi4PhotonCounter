import numpy as np
import re

re_prog_freq = re.compile(r"^([0-9]+[.,]?[0-9]*)\s*([a-zA-Z]*)$")


#
# def parse_frequency(f):
#     # attempt to match the format string
#     match = re_prog_freq.match(f)
#     if not match:
#         raise ValueError(f"Unable to parse string: {f}")
#
#     val, prefix = match.group(1, 2)
#
#     # may raise TypeError if val(str) cannot be cast to val(float)
#     val = float(val)
#     if prefix:
#         # may raise KeyError
#         prefix = prefix_map[prefix]
#     else:
#         prefix = 1.0
#     return val * prefix


class FourierFilter:
    """
    Base class for Fourier filters. Each new filter should extend this class, override __init__ to accept the required
    arguments (different filters may need a different set of parameters).
    The filter function is where the actual filtering is performed, override as needed.
    """
    def __init__(self):
        super(FourierFilter, self).__init__()

        self._params = {}

        self._name = "Abstract Filter"

    def filter(self, xdata, ydata):
        pass

    @property
    def name(self):
        return self._name


######################
# IDEAL FILTER TYPES #
######################
class FFTIdealBandPass(FourierFilter):
    """
    Implements and ideal Band Pass, input ydata is returned as is if the corresponding X values are within
    (center - bandwidth/2, center + bandwidth/2), else 0 is returned
    """
    def __init__(self, center_freq, bandwidth):
        super(FFTIdealBandPass, self).__init__()

        self._params = {
            'cFreq': center_freq,
            'BW': bandwidth
        }

        self._name = f"Band Pass (Ideal) :: f{center_freq}(center) :: f{bandwidth}(BW)"

    def filter(self, xdata, ydata):
        # todo: to improve efficiency these 2 values should be stored rather than computed every time
        xstart = self._params['cFreq'] - self._params['BW'] / 2
        xstop = self._params['cFreq'] + self._params['BW'] / 2
        mask = (xdata > xstart) & (xdata < xstop)
        ydata_zero = np.zeros_like(ydata)
        # ydata is returned where 'mask' is True else 0 is returned.
        return np.where(mask, ydata, ydata_zero)


class FFTIdealBandStop(FourierFilter):
    """
    Implements and ideal Band Stop, input ydata is returned as is if the corresponding X values are outside
    (center - bandwidth/2, center + bandwidth/2), else 0 is returned
    """
    def __init__(self, center_freq, bandwidth):
        super(FFTIdealBandStop, self).__init__()

        self._params = {
            'cFreq': center_freq,
            'BW': bandwidth
        }

        self._name = f"Band Stop (Ideal) :: f{center_freq}(center) :: f{bandwidth}(BW)"

    def filter(self, xdata, ydata):
        # todo: to improve efficiency these 2 values should be stored rather than computed every time
        xstart = self._params['cFreq'] - self._params['BW'] / 2
        xstop = self._params['cFreq'] + self._params['BW'] / 2
        mask = (xdata < xstart) | (xdata > xstop)
        ydata_zero = np.zeros_like(ydata)
        return np.where(mask, ydata, ydata_zero)


class FFTIdealLowPass(FourierFilter):
    """
    Implements and ideal Low Pass, input ydata is returned as is if the corresponding X values are below 'bandwith',
    else 0 is returned.
    """
    def __init__(self, center_freq, bandwidth):
        super(FFTIdealLowPass, self).__init__()

        self._params = {
            'cFreq': 0.0,
            'BW': bandwidth
        }

        self._name = f"Low Pass (Ideal) :: f{0.0}(center) :: f{bandwidth}(BW)"

    def filter(self, xdata, ydata):
        mask = (xdata < self._params['BW'])
        ydata_zero = np.zeros_like(ydata)
        return np.where(mask, ydata, ydata_zero)


class FFTIdealHighPass(FourierFilter):
    """
    Implements and ideal Low Pass, input ydata is returned as is if the corresponding X values are above 'bandwith',
    else 0 is returned.
    """
    def __init__(self, center_freq, bandwidth):
        super(FFTIdealHighPass, self).__init__()

        self._params = {
            'cFreq': 0.0,
            'BW': bandwidth
        }

        self._name = f"High Pass (Ideal) :: f{0.0}(center) :: f{bandwidth}(BW)"

    def filter(self, xdata, ydata):
        mask = (xdata > self._params['BW'])
        ydata_zero = np.zeros_like(ydata)
        return np.where(mask, ydata, ydata_zero)


filter_type_map = {
    'Band Pass (Ideal)': FFTIdealBandPass,
    'Band Stop (Ideal)': FFTIdealBandStop,
    'Low Pass (Ideal)': FFTIdealLowPass,
    'High Pass (Ideal)': FFTIdealHighPass
}
