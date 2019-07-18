import time
import threading as th
import logging
import os.path

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from .gui import MainWindow, DEFAULT_BUFFER_SIZE
from .hamamatsu import Hamamatsu, TRANS
from .buffer import Buffer

DEFAULT_MEASUREMENT_POINTS = 1000000
OUTPATH = os.path.join(os.path.realpath('.'), 'Output')


def _compute_iterations(gtime: str, mes_points: int):
    gates = TRANS[gtime]
    gates = min(gates, mes_points)
    r, iq = mes_points % gates, mes_points // gates

    iterations = iq
    if not r:
        iterations += 1
    return iterations, gates


def _build_date(clock):
    tt = time.gmtime(clock)
    return f'{tt.tm_mday}.{tt.tm_mon}.{tt.tm_year - 2000}_{tt.tm_hour}.{tt.tm_min}.{tt.tm_sec}'


class HamaCtrl(QObject):
    readout_error = pyqtSignal(str)
    readout_complete = pyqtSignal()
    readout_new_point = pyqtSignal()

    def __init__(self, main_view: MainWindow, hardware_model: Hamamatsu):
        super(HamaCtrl, self).__init__()
        self._view = main_view
        self._model = hardware_model

        # hardware setup
        try:
            time.sleep(0.1)
            self._model.open()
        except TimeoutError:
            self._view.warning_box('Unable to initialize Hardware', seppuku=True)
        if not self._model.objs:
            # no hardware found
            self._view.warning_box('No hardware could be detected')

        # data buffer
        self._buffer = Buffer(DEFAULT_BUFFER_SIZE,
                              '',
                              ['time'] + [f'counts_{i}' for i, _ in enumerate(self._model.objs)],
                              save=True)

        self._read_thread = self._regenerate_read_thread()

        self._halt_event = th.Event()
        self._iterations = -1
        self._gates = -1

        # process user actions
        self._view.buffer_size_form.editingFinished.connect(self._on_buffer_size_change)
        self._view.setup_bttn.released.connect(self._on_setup_click)
        self._view.power_bttn.released.connect(self._on_power_click)
        self._view.start_bttn.released.connect(self._on_start_click)
        self._view.save_chkbox.stateChanged.connect(self._on_save_click)

        # connect internal signals
        self.readout_error.connect(self._on_readout_error)
        self.readout_complete.connect(self._view.reset_start_bttn)
        self.readout_new_point.connect(self._view.update_plot)

    def _regenerate_read_thread(self):
        logging.info('Regenerated data readout thread')
        return th.Thread(name='Data Reader', target=self._read_data, daemon=True)

    def _read_data(self):
        logging.info('Starting data readout')

        if self._iterations < 0 or self._gates < 0:
            self.readout_error.emit('Trying to read from un-init hardware')
            self._halt_event.set()

        try:
            self._model.count_start()
        except (TimeoutError, RuntimeError) as e:
            self.readout_error.emit(f'Could not start counting. Msg: {str(e)}')
            self._halt_event.set()

        for i in range(self._iterations):
            if self._halt_event.is_set():
                logging.info('Received readout halt signal')
                self._halt_event.clear()
                break

            data = self._model.read_data(self._gates)
            points = [sum(dd) for dd in data]

            self._buffer.push_back(time.time(), *points)
            self.readout_new_point.emit()

        logging.info('Data readout completed')
        self.readout_complete.emit()

    #########################
    # USER INPUT PROCESSING #
    #########################
    @pyqtSlot()
    def _on_buffer_size_change(self):
        sender = self.sender()
        value = int(sender.text())
        if not value:
            value = DEFAULT_BUFFER_SIZE
        self._buffer.size = value
        logging.info(f'changed buffer size to {value}')

    @pyqtSlot()
    def _on_setup_click(self):
        if not self._model.objs:
            self._view.warning_box('No hardware connected.')
            return
        # get all info we need
        gtime = self._view.gate_time_select.currentText()
        self._iterations, self._gates = _compute_iterations(gtime, DEFAULT_MEASUREMENT_POINTS)
        try:
            # 1 indicates BLOCK_TRANSFER
            self._model.setup(gtime, 1, self._gates)
        except TimeoutError as e:
            self._view.warning_box(str(e))
        else:
            logging.info(f'Set up hardware with parameters {gtime}, {self._iterations}, {self._gates}')

    @pyqtSlot()
    def _on_power_click(self):
        if not self._model.objs:
            self._view.warning_box('No hardware connected.')
            return
        sender = self.sender()
        if sender.isChecked():
            sender.setText('set Power OFF')
            pow_status = True
        else:
            sender.setText('set Power ON')
            pow_status = False

        try:
            self._model.set_power(pow_status)
        except TimeoutError as e:
            self._view.warning_box(str(e))
        else:
            logging.info(f'Set power up status to {pow_status}')

    @pyqtSlot()
    def _on_start_click(self):
        if self._iterations < 0 or self._gates < 0:
            self._view.warning_box('Use the setup button first.')
            return
        if not self._model.objs:
            self._view.warning_box('No hardware connected.')
            return

        sender = self.sender()
        if sender.isChecked():
            try:
                self._read_thread.start()
            except Exception as e:
                self._view.warning_box(str(e))
            else:
                fname = 'Data_' + _build_date(time.time()) + '.csv'
                path = os.path.join(OUTPATH, fname)
                try:
                    self._buffer.set_outpath(path)
                except Exception:
                    self._view.warning_box('Failed to create save file path')
                    self._view.save_chkbox.setChecked(False)
                sender.setText('Stop')
                logging.info('Started data acquisition')
        else:
            self._halt_event.set()
            self._read_thread.join(2.0)
            if self._read_thread.is_alive():
                self._view.warning_box('Failed to stop data readout thread')
            else:
                sender.setText('Start')
                self._read_thread = self._regenerate_read_thread()
                logging.info('Stopped data acquisition')

    @pyqtSlot(int)
    def _on_save_click(self, state):
        if not state:
            self._buffer.set_save(False)
        else:
            self._buffer.set_save(True)

    ##################
    # INTERNAL SLOTS #
    ##################
    @pyqtSlot(str)
    def _on_readout_error(self, msg):
        logging.error(msg)
        self._view.warning_box(msg)

