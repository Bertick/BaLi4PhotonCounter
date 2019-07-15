import threading as th

from PyQt5.QtCore import QSettings, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.QtGui import QDoubleValidator, QIntValidator

from .ui.mainwindow import Ui_MainWindow

from .hamamatsu import minit, GATE_TIMES
from .buffer import Buffer


DEFAULT_Y_RANGE = 100
DEFAULT_BUFFER_SIZE = 200
DEFAULT_X_RANGE = 30.0
TIMINGS = [str(key) for key in GATE_TIMES.keys()]
DEFAULT_PADDING = 0.1
DEFAULT_PLOT_UPDATE = 0.1



class MainWindow(QMainWindow, Ui_MainWindow):
    do_update = pyqtSignal()

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

        # process user actions
        self.y_range_auto.toggled.connect(self._toggle_y_range)
        self.buffer_size_form.editingFinished.connect(self._on_buffer_size_change)
        self.setup_bttn.released.connect(self._on_setup_click)
        self.power_bttn.released.connect(self._on_power_click)

        # internal plotting signals
        self.do_update.connect(self.update_plot)

    def warning_box(self, msg):
        QMessageBox.warning(self, '', msg)

    def init_hardware(self):
        for hardware in self._hw:
            try:
                hardware.read_id()
                print(hardware.uid)
            except TimeoutError:
                self.warning_box(f'timeout occurred during hardware init: handle {hardware.hhandle}')

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
        # print('updating plot')
        # print(self._buffer)
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

    def _plot_reminder(self):
        cond = th.Condition()
        while True:
            self.do_update.emint()
            with cond:
                cond.wait(DEFAULT_PLOT_UPDATE)

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
        raise NotImplementedError('ciccio devo ancora capire come parla sto photon counter')

    def _toggle_hardware_power(self, status):
        for hardware in self._hw:
            try:
                hardware.set_power(status)
            except TimeoutError:
                self.warning_box('timeout occurred during hardware Power toggling')

    @pyqtSlot()
    def _on_power_click(self):
        sender = self.sender()
        if sender.isChecked():
            sender.setText('set Power OFF')
            pow_status = True
        else:
            sender.setText('set Power ON')
            pow_status = False
        self._toggle_hardware_power(pow_status)

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