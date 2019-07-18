import sys
import faulthandler
import atexit

from PyQt5.QtWidgets import QApplication, QInputDialog

from .gui import MainWindow
from .hamamatsu import Hamamatsu
from .hama_ctrl import HamaCtrl

import logging
fmt = "[%(asctime)s] [%(levelname)s] [%(funcName)s(): line %(lineno)s] [PID:%(process)d TID:%(thread)d] %(message)s"
date_fmt = "%d/%m/%Y %H:%M:%S"
logging.basicConfig(format=fmt, datefmt=date_fmt, filename='debug.log', level=logging.DEBUG)

APP_NAME = "BaLi Photon Counter"
APP_VERSION = "0.1"


class PhotonCounter(QApplication):
    """Main class, interconnects the other classes"""
    def __init__(self, sys_argv):
        super(PhotonCounter, self).__init__(sys_argv)

        self._model = Hamamatsu()
        self._view = MainWindow(self._model)
        self._ctrl = HamaCtrl(self._view, self._model)

        self._view.show()

        self.setApplicationName(APP_NAME)
        self.setApplicationVersion(APP_VERSION)


def main():
    with open('traceback_dump.txt', 'w+') as dump_file:
        faulthandler.enable(file=dump_file)

        app = PhotonCounter(sys.argv)

        def _exit_handler():
            try:
                app._model.close()
            except:
                logging.error('Unable to close hardware in _exit_handler')

        atexit.register(_exit_handler)

        try:
            sys.exit(app.exec_())
        except Exception as e:
            logging.error(str(e))





