import sys
import faulthandler
import time
import atexit

from PyQt5.QtWidgets import QApplication, QInputDialog

from .gui import MainWindow

APP_NAME = "BaLi Photon Counter"
APP_VERSION = "0.1"

class PhotonCounter(QApplication):
    """Main class, interconnects the other classes"""
    def __init__(self, sys_argv):
        super(PhotonCounter, self).__init__(sys_argv)

        # ask user for how many units we should work with
        # units, ok = QInputDialog.getInt(None, 'Units number', 'Units number:', value=1, min=1, max=16)
        #
        # if not units or not ok:
        #     sys.exit(0)

        self._main_view = MainWindow(1)

        self._main_view.show()

        self.setApplicationName(APP_NAME)
        self.setApplicationVersion(APP_VERSION)

        # fixme: is this proper ?
        time.sleep(0.25)
        self._main_view.init_hardware()


def main():
    with open('traceback_dump.txt', 'w+') as dump_file:
        faulthandler.enable(file=dump_file)

        app = PhotonCounter(sys.argv)

        def _exit_handler():
            for hh in app._main_view._hw:
                try:
                    hh.set_power(False)
                    hh.close()
                except Exception:
                    pass

        atexit.register(_exit_handler)

        sys.exit(app.exec_())





