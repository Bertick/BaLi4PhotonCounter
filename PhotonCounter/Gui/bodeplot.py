import numpy as np

from pyqtgraph import PlotWidget, mkPen, mkBrush

SYMBOLS = ['t', 't1', 'o', 't2', 't3', 's', 'p', 'h', 'star', '+', 'd']
COLORS = [
    (255, 255, 255),
    (255, 127, 14),
    (255, 0, 0),
    (255, 0, 0),
]


# todo: have specialized plot function for plotting the FFT of a signal
# todo: customize graphics for different curves
class BodePlot(PlotWidget):
    """
    Implements a BodePlot
    """
    def __init__(self, parent=None):
        super(BodePlot, self).__init__(parent=parent)

        # data curves, update rather than re-draw
        self._data_curves = []
        self._fft_curve = None

        # set labels
        self._labels = ['f', '']

        self._units = ['Hz', '']

        self.plotItem.setLabel('bottom', 'f', units='Hz')
        self.plotItem.setLabel('left', '')
        # self.plotItem.setLogMode(True, False)

    def plot(self, xdata, *ydatas):
        for j, ydata in enumerate(ydatas):
            # compute modulus and phase
            mod = np.abs(ydata)
            phs = np.angle(ydata, deg=True)
            # update the plot curve
            try:
                # raises IndexError if this curve was not update before
                self._data_curves[j].setData(xdata, mod)
            except IndexError:
                new_curve = self.plotItem.plot(
                    xdata,
                    mod,
                    pen=COLORS[j % len(COLORS)],
                    symbol=SYMBOLS[j % len(SYMBOLS)],
                    symbolPen=COLORS[j % len(COLORS)],
                    symbolBrush=COLORS[j % len(COLORS)],
                    symbolSize=3
                )
                self._data_curves.append(new_curve)
            # todo: add support to plot phase on secondary y-axis on curve j+1


    def plot_fft(self, xdata, ydata):
        # compute modulus and phase
        mod = np.abs(ydata)
        phs = np.angle(ydata, deg=True)
        # update the plot curve
        try:
            # raises AttributeError
            self._fft_curve.setData(xdata, mod)
        except AttributeError:
            self._fft_curve = self.plotItem.plot(
                xdata,
                mod,
                pen=mkPen((255, 0, 0)),
                # symbol=SYMBOLS[0 % len(SYMBOLS)],
                brush=mkBrush((255, 0, 0)),
                fillLevel=0.0,
            )
        # todo: add support to plot phase on secondary y-axis on curve j+1

        self.plotItem.setYRange(0.0, 1.0, padding=0.0)

    def erase(self):
        for data_curve in self._data_curves:
            data_curve.setData([], [])

    @property
    def fft_curve(self):
        return self._fft_curve