import sys

from fbs_runtime.application_context import cached_property
from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QApplication

from .hamamatsu import Hamamatsu
from .hamamatsu_ctrl import HamamatsuCtrl
from .gui import MainWindow

import logging
logging.basicConfig(filename='BaLi4PhotonCounter_log.log', level=logging.DEBUG)

APP_NAME = "BaLi Photon Counter"
APP_VERSION = "0.1"


class BaLiContext(ApplicationContext):
    @cached_property
    def app(self):
        return PhotonCounter(sys.argv)


class PhotonCounter(QApplication):
    """Main class, interconnects the other classes"""
    def __init__(self, sys_argv):
        super(PhotonCounter, self).__init__(sys_argv)

        self._hardware = Hamamatsu()
        self._main_view = MainWindow(self._hardware)
        self._cam_ctrl = HamamatsuCtrl(self._main_view, self._hardware)

        self._main_view.show()

        self.setApplicationName(APP_NAME)
        self.setApplicationVersion(APP_VERSION)


def main():
    app_context = BaLiContext()
    status_code = -1

    try:
        status_code = app_context.app.exec_()
    except Exception as e:
        logging.error(e)
    finally:
        sys.exit(status_code)










