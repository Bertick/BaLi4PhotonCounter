import logging
import time
import threading as th
import os.path

import numpy as np

from PyQt5.QtCore import QSettings, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QMainWindow

from .Gui.mainwin import Ui_MainWindow
from .hamamatsu import GATE_TIMES, Hamamatsu
from .buffer import SimpleBuffer
from .fourieranalysis_gui import FourierGui

DATAFOLDER = os.path.join(os.path.realpath('.'), 'Data')

DEFAULT_DISPLAY_TIME = 10.0
DEFAULT_BUFFER_SIZE = 1000

TIMINGS = [str(key) for key in GATE_TIMES.keys()]


def _build_date():
    tt = time.gmtime()
    return f'{tt.tm_mday:02d}.{tt.tm_mon:02d}.{tt.tm_year - 2000:02d}_{tt.tm_hour:02d}.{tt.tm_min:02d}.{tt.tm_sec:02d}'


# todo: instead of printing 'e' we should add some extra info like: 'failed to start readout - msg: {str(e)}'
# todo: all messages being written by dbg_console should end with a dot
# todo: all Exception messages should not end with a dot (it should be added when writing to dbg_console)
class PhotonCounterGui(QMainWindow, Ui_MainWindow):
    """
    Implements GUI and logic for main window
    """
    sig_update_plot = pyqtSignal()

    def __init__(self):
        super(PhotonCounterGui, self).__init__()

        # setup the UI code
        self.setupUi(self)
        self.read_settings()

        # data
        # hardware is initialized to Hamamatsu() just to have type checking from PyCharm
        self._hardware = Hamamatsu()
        # create a data readout thread
        self._readout_thread = self._regenerate_read_thread()
        self._readout_halt_event = th.Event()

        # points buffer
        self._data_buffer = SimpleBuffer(
            DEFAULT_BUFFER_SIZE,
            os.path.join(DATAFOLDER, f'log_{_build_date()}.csv'),
            ['Counts'],
            save=True
        )

        # FFT analyser GUI
        self.fft_analysis = FourierGui()

        # todo: organize better how these values are stored ... don't leave them randomly around like this
        # these are used for plotting the absolute min/max of moving average
        self._mvavg_min = np.inf
        self._mvavg_max = -np.inf

        # set plot labels and standard display time
        self.scroll_plot.labels = ['Time', 'Counts']
        self.scroll_plot.display_time = DEFAULT_DISPLAY_TIME

        # setup parameters widgets
        self.param_gate_time.addItems(TIMINGS)
        self.param_gate_time.setCurrentIndex(TIMINGS.index('100MS'))
        self.display_time_box.setValue(DEFAULT_DISPLAY_TIME)
        self.buffer_size_box.setValue(DEFAULT_BUFFER_SIZE)

        # connect QtSignals to proper callback functions
        self.display_time_box.valueChanged.connect(self._on_display_time_change)
        self.buffer_size_box.valueChanged.connect(self._on_buffer_size_change)
        self.clearplot_bttn.pressed.connect(self._on_clear_plot_click)
        #
        self.param_connect.pressed.connect(self._on_connect)
        #
        self.param_set_gatetime.setDisabled(True)
        self.param_set_gatetime.pressed.connect(self._on_set_gatetime)
        #
        self.param_toggle_power.setDisabled(True)
        self.param_toggle_power.pressed.connect(self._on_toggle_power)
        #
        self.param_toggle_acquisition.setDisabled(True)
        self.param_toggle_acquisition.pressed.connect(self._on_toggle_acquisition)
        #
        self.mvavg_minmax_checkbox.toggled.connect(self._on_mvavg_minmax_toggle)
        #
        self.fft_push_bttn.clicked.connect(self._on_fft_bttn_click)

        # internal plot update signal
        self.sig_update_plot.connect(self._update_plot)

    ####################
    # CLIENT INTERFACE #
    ####################
    def add_data(self, values):
        """
        Called by data readout thread when new data is available
        """
        # add to buffer
        for val in values:
            self._data_buffer.push_back(val)
        # signal for plot update (this should happen across threads)
        # allows the data readout thread to push new data in buffer
        # but keeps the Plot update in the main Thread (this is mandatory)
        self.sig_update_plot.emit()

    #############
    # INTERNALS #
    #############
    @pyqtSlot()
    def _update_plot(self):
        # compute amount of points to display
        gate_time = self._hardware.get_gatetime_data()[2]
        npoints = int((self.scroll_plot.display_time // gate_time) + 1)
        # if the buffer is too small we need to limit the number of points to what we have
        npoints = min(npoints, len(self._data_buffer.containers[0]))

        xdata = (np.mgrid[0:npoints] - npoints) * gate_time

        # is this cast to list necessary?
        ydata_full = list(self._data_buffer.containers[0])
        ydata = ydata_full[-npoints:]

        # moving average computation
        ydata_avg = None
        if self.mvavg_checkbox.isChecked():
            ydata_avg = self._get_moving_avg(ydata_full)[-npoints:]

            self._mvavg_max = max(self._mvavg_max, np.max(ydata_avg))
            self._mvavg_min = min(self._mvavg_min, np.min(ydata_avg))

        # moving average absolute min and max lines
        ydata_avg_min = None
        ydata_avg_max = None
        if self.mvavg_minmax_checkbox.isChecked():
            ydata_avg_min = np.ones_like(xdata) * self._mvavg_min
            ydata_avg_max = np.ones_like(xdata) * self._mvavg_max

        # update plot
        self.scroll_plot.plot(
            xdata,
            ydata,
            ydata_avg,
            ydata_avg_min,
            ydata_avg_max
        )

        # update fft view if enabled:
        if self.fft_analysis.isActiveWindow():
            self.fft_analysis.process(xdata, ydata)

    #############################
    # CALLBACK FOR USER ACTIONS #
    #############################
    @pyqtSlot()
    def _on_display_time_change(self):
        self.scroll_plot.display_time = self.display_time_box.value()
        self.fft_analysis.set_display_time(self.display_time_box.value())

    @pyqtSlot()
    def _on_buffer_size_change(self):
        self._data_buffer.size = self.buffer_size_box.value()

    @pyqtSlot()
    def _on_clear_plot_click(self):
        self.scroll_plot.erase()

    @pyqtSlot(bool)
    def _on_mvavg_minmax_toggle(self, checked):
        if not checked:
            self._mvavg_max = -np.inf
            self._mvavg_min = np.inf

    @pyqtSlot(bool)
    def _on_fft_bttn_click(self, checked):
        self.fft_analysis.show()

    # Hardware interaction
    @pyqtSlot()
    def _on_connect(self):
        try:
            self._hardware = Hamamatsu.open()
        except ValueError as e:
            self.dbg_console.write(e, log=True, level=logging.WARNING)
        except (TimeoutError, RuntimeError) as e:
            self.dbg_console.write(e, log=True, level=logging.ERROR)
        else:
            self.dbg_console.write(f'Detected hardware uid: {self._hardware.uid}.', log=True, level=logging.INFO)
            # enable the next button
            self.param_set_gatetime.setEnabled(True)

    @pyqtSlot()
    def _on_set_gatetime(self):
        gtime = self.param_gate_time.currentText()
        self._hardware.gate_time = gtime
        # attempt to set the hardware params
        try:
            # 1 indicates BLOCK_TRANSFER
            self._hardware.setup(mode=1)
        except (RuntimeError, TimeoutError) as e:
            self.dbg_console.write(e, log=True, level=logging.ERROR)
        else:
            self.dbg_console.write(f'Hardware Gate time set to {gtime}.', log=True, level=logging.INFO)
            # enable the next button
            self.param_toggle_power.setEnabled(True)

    @pyqtSlot()
    def _on_toggle_power(self):
        if self._hardware.is_powered:
            new_pow_status = False
        else:
            new_pow_status = True

        try:
            self._hardware.set_power(new_pow_status)
        except (RuntimeError, TimeoutError) as e:
            self.dbg_console.write(e, log=True, level=logging.ERROR)
        else:
            curr_txt = 'ON' if new_pow_status else 'OFF'
            next_txt = 'ON' if not new_pow_status else 'OFF'
            self.dbg_console.write(f'Successfully set power {curr_txt}.', log=True, level=logging.INFO)
            # set the button text for next action
            self.param_toggle_power.setText(f'Set Power {next_txt}')
            # enable the next button
            self.param_toggle_acquisition.setEnabled(True)

    @pyqtSlot()
    def _on_toggle_acquisition(self):
        if not self._hardware.is_counting:
            try:
                self._hardware.count_start()
            except (RuntimeError, TimeoutError) as e:
                self.dbg_console.write(f'Could not start counting. Msg: {str(e)}.', log=True, level=logging.ERROR)
            else:
                # setup the buffer filepath and header information
                fname = f'log_{_build_date()}.csv'
                path = os.path.join(DATAFOLDER, fname)
                self._data_buffer.filepath = path
                self._data_buffer.header_extra = f"# GATE TIME {self._hardware.gate_time}."

                self.dbg_console.write('Starting data readout.', log=True, level=logging.INFO)
                self._readout_thread.start()

                self.param_toggle_acquisition.setText('Stop Acquisition')
                # disable connect, power and gate time buttons
                self.param_connect.setEnabled(False)
                self.param_set_gatetime.setEnabled(False)
                self.param_toggle_power.setEnabled(False)
        else:
            # stop readout thread
            self._readout_halt_event.set()
            # todo: this timeout time should not be hardcoded
            self._readout_thread.join(1.0)
            # I've noticed that most of the time the Hardware library fucks up and the data Thread does not
            # rejoin the main thread. So check if that happened:
            if self._readout_thread.is_alive():
                self.dbg_console.write('Failed to stop data readout thread correctly.',
                                       log=True,
                                       level=logging.WARNING)
            # Even if readout thread didn't stop correctly we can hope that the Garbage collector will take care of it.
            # So just generate a new thread and the old one should have zero references left.
            self._readout_thread = self._regenerate_read_thread()
            # Attempt to stop Hardware from counting photons
            try:
                self._hardware.count_stop()
            except (RuntimeError, TimeoutError) as e:
                self.dbg_console.write(f'Could not stop counting unit. Msg: {str(e)}.', log=True, level=logging.ERROR)
            else:
                self.dbg_console.write('Data readout stopped.', log=True, level=logging.INFO)
                self.param_toggle_acquisition.setText('Start Acquisition')
                # enable connect, power and gate time buttons
                self.param_connect.setEnabled(True)
                self.param_set_gatetime.setEnabled(True)
                self.param_toggle_power.setEnabled(True)

    #############
    # INTERNALS #
    #############
    def _regenerate_read_thread(self):
        self.dbg_console.write('Initialized new data-readout thread.', log=True, level=logging.INFO)
        return th.Thread(name='Data Reader', target=self._data_readout, daemon=True)

    def _data_readout(self):
        self.dbg_console.write('Starting data readout.', log=True, level=logging.INFO)
        # compute delay between calls
        # todo: do we really need this? shouldn't the hardware take care of the delay between calls?
        _, num_gates, gate_time = self._hardware.get_gatetime_data()
        delay = num_gates * gate_time * 0.9

        while True:
            # check if the 'Halt event' is set, if yes break from the loop.
            if self._readout_halt_event.is_set():
                self._readout_halt_event.clear()
                self.dbg_console.write('Data readout thread received halt signal.', log=True, level=logging.INFO)
                break

            try:
                data = self._hardware.read_data()
            except (RuntimeError, TimeoutError) as e:
                self.dbg_console.write(e, log=True, level=logging.ERROR)
                break
            else:
                self.add_data(data)
            #time.sleep(delay)

        self.dbg_console.write('Data readout completed.', log=True, level=logging.INFO)

    def _get_moving_avg(self, data):
        n = int(self.mvavg_spinbox.value())
        if len(data) < n:
            return data
        avg = np.convolve(data, np.ones(n), 'valid') / n
        return np.concatenate((data[:n-1], avg))

    ########################
    # SETTINGS AND CLOSING #
    ########################
    def save_settings(self):
        settings = QSettings('BaLi', 'PhotonCounter')
        settings.setValue('geometry', self.saveGeometry())
        settings.setValue('state', self.saveState())
        settings.setValue('splitter_vert/geometry', self.splitter_vert.saveGeometry())
        settings.setValue('splitter_vert/state', self.splitter_vert.saveState())
        settings.setValue('splitter_horiz/geometry', self.splitter_horiz.saveGeometry())
        settings.setValue('splitter_horiz/state', self.splitter_horiz.saveState())

    def read_settings(self):
        settings = QSettings('BaLi', 'PhotonCounter')
        try:
            self.restoreGeometry(settings.value("geometry"))
            self.restoreState(settings.value("state"))
            self.splitter_vert.restoreGeometry(settings.value("splitter_vert/geometry"))
            self.splitter_vert.restoreState(settings.value("splitter_vert/state"))
            self.splitter_horiz.restoreGeometry(settings.value("splitter_horiz/geometry"))
            self.splitter_horiz.restoreState(settings.value("splitter_horiz/state"))
        except TypeError:
            pass

    def closeEvent(self, event):
        self.save_settings()

        self.fft_analysis.close()

        # try to put hardware in safe condition
        if self._hardware.is_counting:
            self._readout_halt_event.set()
            self._hardware.count_stop()

        self._hardware.set_power(False)
        self._hardware.close()

        super().closeEvent(event)
