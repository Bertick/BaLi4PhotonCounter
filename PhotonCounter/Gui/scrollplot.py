from pyqtgraph import PlotWidget, mkPen, mkBrush
from itertools import islice

# SYMBOLS = ['t', 't1', 'o', 't2', 't3', 's', 'p', 'h', 'star', '+', 'd']
SYMBOLS = ['o', 'o', None, None]
COLORS = [
    (255, 255, 255),
    (255, 127, 14),
    (255, 0, 0),
    (255, 0, 0),
]

# COLORS = [
#     (31, 119, 180),
#     (255, 127, 14),
#     (44, 160, 44),
#     (214, 39, 40),
#     (148, 103, 189),
#     (140, 86, 75),
#     (227, 119, 194),
#     (127, 127, 127),
#     (188, 189, 34),
#     (23, 190, 207)
# ]


class ScrollPlot(PlotWidget):
    def __init__(self, parent=None, labels=tuple(), units=tuple(), units_prefixes=tuple()):
        super(ScrollPlot, self).__init__(parent=parent)

        # data curve, update rather than re-draw
        self._data_curves = []

        # set labels
        if not labels:
            labels = ['time', 'y']
        self._labels = labels

        # set labels units
        if not units:
            units = ['s', '']
        self._units = units

        # set labels units prefixes
        if not units_prefixes:
            units_prefixes = ['', '']
        self._units_prefixes = units_prefixes

        self._update_labels()

        # display options
        self._displaytime = 30.0

        self._colours = {
            'red': (255, 0, 0),
            'orange': (255, 112, 0),
            'yellow': (255, 255, 0),
            'green': (0, 255, 0),
            'blue': (0, 0, 255),
            'magenta': (255, 0, 255),
            'white': (255, 255, 255),
            'black': (0, 0, 0)
        }

    ####################
    # CLIENT INTERFACE #
    ####################
    def plot(self, xdata, *ydatas):
        # get last time
        tfin = xdata[-1]
        tini = tfin - self.display_time
        # start iterating from the end and see which points are within display_time
        # todo: can't we implement some quick-sort version of this? Also this is an ordered list
        i = 0
        for i, tt in enumerate(reversed(xdata)):
            if tt < tini:
                break
        # filter only to the last values
        ll = len(xdata)
        xx = list(islice(xdata, ll-i, ll))

        for j, ydata in enumerate(ydatas):
            # update the plot curve
            try:
                # raises TypeError if data is None (used in case we don't want to update this curve any more)
                yy = list(islice(ydata, ll-i, ll))
                # raises IndexError if this curve was not update before
                self._data_curves[j].setData(xx, yy)

            except TypeError:
                try:
                    self._data_curves[j].setData([], [])
                except IndexError:
                    continue

            except IndexError:
                new_curve = self.plotItem.plot(
                    xx,
                    yy,
                    pen=COLORS[j % len(COLORS)],
                    symbol=SYMBOLS[j % len(SYMBOLS)],
                    symbolPen=COLORS[j % len(COLORS)],
                    symbolBrush=COLORS[j % len(COLORS)],
                    symbolSize=3
                )
                self._data_curves.append(new_curve)

    def erase(self):
        for data_curve in self._data_curves:
            data_curve.setData([], [])

    @property
    def display_time(self):
        return self._displaytime

    @display_time.setter
    def display_time(self, value):
        if value < 0:
            value = -value
        # set the value
        self._displaytime = value

    def set_line_colour(self, c='blue'):
        self._data_curve.setPen(mkPen(self._colours[c]))
        self._data_curve.setSymbolPen(mkPen(self._colours[c]))

    def set_symbol_colour(self, c='blue'):
        self._data_curve.setSymbolBrush(mkBrush(self._colours[c]))

    def set_colour(self, c='blue'):
        self.set_line_colour(c)
        self.set_symbol_colour(c)

    ##############
    # SET LABELS #
    ##############
    def _update_labels(self):
        self.plotItem.setLabel('bottom', self._labels[0], units=self._units[0], unitPrefix=self._units_prefixes[0])
        self.plotItem.setLabel('left', self._labels[1], units=self._units[1], unitPrefix=self._units_prefixes[1])

    @property
    def labels(self):
        return self._labels

    @labels.setter
    def labels(self, ll):
        self._labels = ll
        self._update_labels()

    @property
    def units(self):
        return self._units

    @units.setter
    def units(self, uu):
        self._units = uu
        self._update_labels()

    @property
    def unit_prefixes(self):
        return self._units_prefixes

    @unit_prefixes.setter
    def unit_prefixes(self, uu):
        self._units_prefixes = uu
        self._update_labels()


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    import numpy as np

    app = QApplication(sys.argv)

    gui = ScrollPlot()

    gui.show()

    # times = [1, 2, 3, 4, 5, 6]
    # ydata1 = [1, 2, 3, 4, 5, 6]
    # ydata2 = [3, 3, 3, 4, 4, 4]
    # ydata3 = [x + 5 for x in ydata1]
    #
    # gui.plot(times, ydata1, ydata2, ydata3)

    times = range(200)
    data_tot = [np.random.rand() + i for i in range(200)]

    N = 34

    data_tot = list(reversed(data_tot[-N:]))
    times = np.array(times[-N:]) - times[-1]

    gui.plot(times, data_tot, [y*2 for y in data_tot])

    sys.exit(app.exec_())





