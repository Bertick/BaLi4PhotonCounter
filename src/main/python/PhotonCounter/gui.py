import sys
from threading import Thread

from PyQt5.QtCore import Qt, QSettings, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.QtGui import QPen, QBrush
from PyQt5.QtGui import QDoubleValidator, QIntValidator

from .ui.mainwindow import Ui_MainWindow

from .hamamatsu import Hamamatsu
from .buffer import Buffer


DEFAULT_Y_RANGE = 100
DEFAULT_BUFFER_SIZE = 200
DEFAULT_X_RANGE = 30.0


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, hardware_model: Hamamatsu):
        super(MainWindow, self).__init__()

        self._hardware = hardware_model

        # setup the UI code
        self.setupUi(self)
        self.read_settings()

        # set the validator for the LineEdit(s)
        self.y_range_form.setValidator(QDoubleValidator())
        self.buffer_size_form.setValidator(QIntValidator())
        self.display_secs_form.setValidator(QDoubleValidator())

        # set defaults values
        self.y_range_form.setText(str(DEFAULT_Y_RANGE))
        self.buffer_size_form.setText(str(DEFAULT_BUFFER_SIZE))
        self.display_secs_form.setText(str(DEFAULT_X_RANGE))

        # prepare the PlotWidget
        self.count_graph.plotItem.setTitle("Counts")
        self.count_graph.plotItem.setLabel('bottom', 'time', 'sec')
        self.count_graph.plotItem.setLabel('left', 'Counts/Gate', '')

        # data buffer
        # todo: output_path should be a real file and save = True (user decision)
        self._buffer = Buffer(DEFAULT_BUFFER_SIZE, '', ['time', 'counts'])

        # process user actions
        self.y_range_auto.toggled.connect(self._toggle_y_range)

    def warning_box(self, msg):
        QMessageBox.warning(self, '', msg)

    def plot_data(self, times, values):
        tt = [t - times[-1] for t in times]
        self.count_graph.plotItem.clear()
        self.count_graph.plotItem.plot(tt, values,
                                       pen=(0, 0, 200),
                                       symbolBrush=(0, 0, 200),
                                       symbolPen='w',
                                       symbol='o',
                                       symbolSize=2)

        vbox = self.count_graph.plotItem.getViewBox()

        xmax = float(self.display_secs_form.text())
        if not xmax or xmax == 0.0:
            xmax = -30.0
        if xmax > 0:
            xmax = -xmax

        vbox.setXRange(xmax, 0.1 * abs(max(tt)-min(tt)), padding=0)

        if not self.y_range_auto.isChecked():
            ymax = float(self.y_range_form.text())
            if not ymax:
                ymax = 1.0
            vbox.setYRange(0, ymax, padding=0)

    def init_hardware(self, click):
        try:
            self._hardware.open()
            self._hardware.read_id()
            print(self._hardware.uid)
        except TimeoutError:
            self.warning_box('timeout occurred')

    #########################
    # USER INPUT PROCESSING #
    #########################
    @pyqtSlot(bool)
    def _toggle_y_range(self, checked):
        # if auto range is enabled, disable the user input form
        self.y_range_form.setDisabled(checked)

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