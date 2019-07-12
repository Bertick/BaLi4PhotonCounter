import sys
from threading import Thread

from PyQt5.QtCore import Qt, QSettings, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QMainWindow, QGraphicsEllipseItem, QGraphicsRectItem
from PyQt5.QtGui import QPen, QBrush
from PyQt5.QtGui import QDoubleValidator, QIntValidator

from .ui.mainwindow import Ui_MainWindow

from .hamamatsu import Hamamatsu


class MainWindow(QMainWindow, Ui_MainWindow):
    @pyqtSlot(bool)
    def _toggle_y_range(self, checked):
        self.y_range_form.setDisabled(checked)

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

        # if auto range is enabled, disable the user input form
        self.y_range_auto.toggled.connect(self._toggle_y_range)

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
