from queue import Queue, Full
from collections import deque
from threading import Thread
import time
import os
import os.path

from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QMessageBox

from .gui import MainWindow
from .hamamatsu import Hamamatsu

class HamamatsuCtrl(QObject):
    def __init__(self, view: MainWindow, hardware_model: Hamamatsu):
        super(HamamatsuCtrl, self).__init__()

        self._view = view
        self._hardware = hardware_model













