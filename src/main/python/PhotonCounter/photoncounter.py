import sys
import faulthandler
import time

from fbs_runtime.application_context import cached_property
from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtWidgets import QApplication

from .hamamatsu import Hamamatsu
from .gui import MainWindow

# import logging
# logging.basicConfig(filename='BaLi4PhotonCounter_log.log', level=logging.DEBUG)

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

        self._main_view.show()

        self.setApplicationName(APP_NAME)
        self.setApplicationVersion(APP_VERSION)

        # fixme: is this proper ?
        time.sleep(0.25)
        self._main_view.init_hardware()

def main():
    with open('traceback_dump.txt', 'w+') as dump_file:
        faulthandler.enable(file=dump_file)

        app_context = BaLiContext()

        sys.exit(app_context.app.exec_())







