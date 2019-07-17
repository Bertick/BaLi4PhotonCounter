import time
import threading as th
import sys

from PyQt5.QtCore import QSettings, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.QtGui import QDoubleValidator, QIntValidator

from .ui.mainwindow import Ui_MainWindow

from .hamamatsu import minit, GATE_TIMES, TRANS
from .buffer import Buffer

# PLOT CONSTANTS
DEFAULT_Y_RANGE = 100
DEFAULT_BUFFER_SIZE = 200
DEFAULT_X_RANGE = 30.0
DEFAULT_PADDING = 0.1
DEFAULT_PLOT_UPDATE = 0.1

# SETUP
TIMINGS = [str(key) for key in GATE_TIMES.keys()]
DEFAULT_MEASUREMENT_POINTS = 500000


def _compute_iterations(gtime: str, mes_points: int):
    gates = TRANS[gtime]
    gates = min(gates, mes_points)
    r, iq = mes_points % gates, mes_points // gates

    iterations = iq
    if not r:
        iterations += 1
    return iterations, gates


class MainWindow(QMainWindow, Ui_MainWindow):
    do_update = pyqtSignal()
    reading_finish = pyqtSignal()

    def __init__(self, n_units):
        super(MainWindow, self).__init__()

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
        self.gate_time_select.addItems(TIMINGS)

        # prepare the PlotWidget
        self.count_graph.plotItem.setTitle("Counts")
        self.count_graph.plotItem.setLabel('bottom', 'time', 'sec')
        self.count_graph.plotItem.setLabel('left', 'Counts/Gate', '')

        # hardware setup
        self._hw = minit(n_units)
        if not self._hw:
            # no hardware found
            self.warning_box('No hardware could be detected')

        # data buffer
        # todo: output_path should be a real file and save = True (user decision)
        self._buffer = Buffer(DEFAULT_BUFFER_SIZE, '', ['time'] + [f'counts_{i}' for i in range(len(self._hw))])

        self._read_thread = th.Thread(name='reader', target=self._read_data)
        self._iterations = -1
        self._gates = -1

        # process user actions
        self.y_range_auto.toggled.connect(self._toggle_y_range)
        self.buffer_size_form.editingFinished.connect(self._on_buffer_size_change)
        self.setup_bttn.released.connect(self._on_setup_click)
        self.power_bttn.released.connect(self._on_power_click)
        self.start_bttn.released.connect(self._on_start_click)

        # internal plotting signals
        self.do_update.connect(self.update_plot)
        self.reading_finish.connect(self._reset_start_bttn)

    def warning_box(self, msg, seppuku=False):
        if seppuku:
            msg = msg + '\nSeppuku engaged!'
            QMessageBox.warning(self, '', msg)
            sys.exit(-1)
        else:
            QMessageBox.warning(self, '', msg)

    def init_hardware(self):
        for hardware in self._hw:
            try:
                hardware.read_id()
                print(hardware.uid)
            except TimeoutError:
                self.warning_box(f'timeout occurred during hardware init: handle {hardware.hhandle}', seppuku=True)

    ############
    # PLOTTING #
    ############
    def _plot_data(self, times, values):
        tt = [t - times[-1] for t in times]
        self.count_graph.clear()
        self.count_graph.plot(tt, values,
                              pen=(0, 0, 200),
                              symbolBrush=(0, 0, 200),
                              symbolPen='w',
                              symbol='o',
                              symbolSize=2)
        vbox = self.count_graph.plotItem.getViewBox()
        xmax_str = self.display_secs_form.text()
        if not xmax_str:
            xmax = DEFAULT_X_RANGE
        else:
            xmax = float(xmax_str)
        if xmax > 0:
            xmax = -xmax
        xmax = max(xmax, min(tt))
        vbox.setXRange(xmax, DEFAULT_PADDING * abs(max(tt)-min(tt)), padding=0)
        if not self.y_range_auto.isChecked():
            ymax = float(self.y_range_form.text())
            if not ymax:
                ymax = DEFAULT_Y_RANGE
        else:
            ymax = max(values) * (1.0 + DEFAULT_PADDING)
        if ymax < 0:
            ymax = -ymax
        vbox.setYRange(0, ymax, padding=0)

    @pyqtSlot()
    def update_plot(self):
        print('updating plot')
        print(self._buffer)
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
        for values in vs:
            self._plot_data(ts, values)

    def _read_data(self):
        if self._iterations < 0 or self._gates < 0:
            raise RuntimeError('Trying to read from un-init hardware')

        for hardware in self._hw:
            hardware.count_start()

        for i in range(self._iterations):
            points = [0.0] * len(self._hw)
            for hi, hardware in enumerate(self._hw):
                if self._ha
                data = hardware.read_data(self._gates)
                points[hi] = sum(data) / self._gates

            self._buffer.push_back(time.time(), *points)
            self.do_update.emit()
        self.reading_finish.emit()

    #########################
    # USER INPUT PROCESSING #
    #########################
    @pyqtSlot(bool)
    def _toggle_y_range(self, checked):
        # if auto range is enabled, disable the user input form
        self.y_range_form.setDisabled(checked)

    @pyqtSlot()
    def _on_buffer_size_change(self):
        sender = self.sender()
        value = int(sender.text())
        if not value:
            value = DEFAULT_BUFFER_SIZE
        self._buffer.size = value

    @pyqtSlot()
    def _on_setup_click(self):
        if not self._hw:
            self.warning_box('No hardware connected.')
            return
        # get all info we need
        gtime = self.gate_time_select.currentText()
        self._iterations, self._gates = _compute_iterations(gtime, DEFAULT_MEASUREMENT_POINTS)
        for hardware in self._hw:
            hardware.setup(gtime, 1, self._gates)

    def _toggle_hardware_power(self, status):
        for hardware in self._hw:
            try:
                hardware.set_power(status)
            except TimeoutError:
                self.warning_box('timeout occurred during hardware Power toggling')

    @pyqtSlot()
    def _on_power_click(self):
        if not self._hw:
            self.warning_box('No hardware connected.')
            return
        sender = self.sender()
        if sender.isChecked():
            sender.setText('set Power OFF')
            pow_status = True
        else:
            sender.setText('set Power ON')
            pow_status = False
        self._toggle_hardware_power(pow_status)

    @pyqtSlot()
    def _on_start_click(self):
        if self._iterations < 0 or self._gates < 0:
            self.warning_box('Use the setup button first.')
            return

        if not self._hw:
            self.warning_box('No hardware connected.')
            return
        sender = self.sender()
        if sender.isChecked():
            try:
                self._read_thread.start()
            except Exception as e:
                self.warning_box(str(e))
            sender.setText('Stop')
        else:
            for hardware in self._hw:
                hardware.count_stop()
            sender.setText('Start')

    @pyqtSlot()
    def _reset_start_bttn(self):
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