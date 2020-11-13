import logging
import sys


from PyQt5.QtCore import QSettings, pyqtSlot
from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.QtGui import QDoubleValidator, QIntValidator

from .ui.mainwindow import Ui_MainWindow

from .hamamatsu import Hamamatsu, GATE_TIMES

# PLOT CONSTANTS
DEFAULT_Y_RANGE = 100
DEFAULT_BUFFER_SIZE = 200
DEFAULT_X_RANGE = 30.0
DEFAULT_PADDING = 0.1
DEFAULT_PLOT_UPDATE = 0.1

TIMINGS = [str(key) for key in GATE_TIMES.keys()]

COLOURS = [(0, 200, 0), (200, 0, 0), (0, 0, 200), (255, 180, 0), (255, 0, 180)]


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, hardware_model: Hamamatsu):
        super(MainWindow, self).__init__()

        self._model = hardware_model

        # setup the UI code
        self.setupUi(self)
        self.read_settings()

        # set the validator for the LineEdit(s)
        self.buffer_size_form.setValidator(QIntValidator())
        self.display_secs_form.setValidator(QDoubleValidator())

        # set defaults values
        self.buffer_size_form.setText(str(DEFAULT_BUFFER_SIZE))
        self.display_secs_form.setText(str(DEFAULT_X_RANGE))
        self.gate_time_select.addItems(TIMINGS)
        self.gate_time_select.setCurrentIndex(TIMINGS.index('100MS'))

        # prepare the PlotWidget
        self.count_graph.plotItem.setTitle("Counts")
        self.count_graph.plotItem.setLabel('bottom', 'time', 'sec')
        self.count_graph.plotItem.setLabel('left', 'Counts/Gate', '')

    def warning_box(self, msg, seppuku=False):
        if seppuku:
            msg = msg + '\nSeppuku engaged!'
            QMessageBox.warning(self, '', msg)
            logging.error(msg)
            sys.exit(-1)
        else:
            QMessageBox.warning(self, '', msg)
            logging.warning(msg)

    ############
    # PLOTTING #
    ############
    def _plot_data(self, times, values, colour):
        tt = [t - times[-1] for t in times]

        # vbox = self.count_graph.plotItem.getViewBox()
        xmax_str = self.display_secs_form.text()
        if not xmax_str:
            xmax = DEFAULT_X_RANGE
        else:
            xmax = float(xmax_str)
        if xmax > 0:
            xmax = -xmax
        # xmax = max(xmax, min(tt))

        pck = [(t, v) for t, v in zip(tt, values) if t >= xmax]
        tt, values = zip(*pck)

        self.count_graph.clear()
        self.count_graph.plot(tt, values,
                              pen=colour,
                              symbolBrush=colour,
                              symbolPen='w',
                              symbol='o',
                              symbolSize=4)
        # if not self.y_range_auto.isChecked():
        #     ymax = float(self.y_range_form.text())
        #     if not ymax:
        #         ymax = DEFAULT_Y_RANGE
        # else:
        #     ymax = max(values) * (1.0 + DEFAULT_PADDING)
        # if ymax < 0:
        #     ymax = -ymax
        # ymin = min(values) * (1.0 - DEFAULT_PADDING)
        # vbox.setYRange(ymin, ymax, padding=0)

    @pyqtSlot()
    def update_plot(self):
        bb_len = len(self._buffer)
        if bb_len:
            bb_width = len(self._buffer[0])
        else:
            bb_width = 0

        if not bb_len or not bb_width:
            return

        # time series (always first place)
        ts = [i[0] for i in self._buffer]
        # value series
        vs = [[i[k] for i in self._buffer] for k in range(1, bb_width)]

        # plot 'em
        for i, values in enumerate(vs):
            c = COLOURS[i % len(COLOURS)]
            self._plot_data(ts, values, c)

    def reset_start_bttn(self):
        self.start_bttn.setChecked(False)

    ########################
    # SETTINGS AND CLOSING #
    ########################
    def save_settings(self):
        settings = QSettings('BaLi', 'PhotonCounter')
        settings.setValue('geometry', self.saveGeometry())
        settings.setValue('windowState', self.saveState())
        settings.setValue('splitter/geometry', self.splitter.saveGeometry())
        settings.setValue('splitter/state', self.splitter.saveState())

    def read_settings(self):
        settings = QSettings('BaLi', 'PhotonCounter')
        if settings.value("geometry") is not None:
            self.restoreGeometry(settings.value("geometry"))
        if settings.value("windowState") is not None:
            self.restoreState(settings.value("windowState"))
        if settings.value("splitter/geometry") is not None:
            self.splitter.restoreGeometry(settings.value("splitter/geometry"))
        if settings.value("splitter/state") is not None:
            self.splitter.restoreState(settings.value("splitter/state"))

    def closeEvent(self, event):
        self.save_settings()
        super(MainWindow, self).closeEvent(event)