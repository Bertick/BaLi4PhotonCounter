import sys
import faulthandler

from PyQt5.QtWidgets import QApplication

from PhotonCounter.photoncounter_gui import PhotonCounterGui

import logging
fmt = "[%(asctime)s] [%(levelname)s] [%(funcName)s(): line %(lineno)s] [PID:%(process)d TID:%(thread)d] %(message)s"
date_fmt = "%d/%m/%Y %H:%M:%S"
logging.basicConfig(format=fmt, datefmt=date_fmt, filename='debug.log', level=logging.DEBUG)

APP_NAME = "BaLi Photon Counter"
APP_VERSION = "0.2"


class PhotonCounter(QApplication):
    def __init__(self, sys_argv):
        super(PhotonCounter, self).__init__(sys_argv)

        self.gui = PhotonCounterGui()
        self.gui.show()

        self.setApplicationName(APP_NAME)
        self.setApplicationVersion(APP_VERSION)


if __name__ == '__main__':
    with open('traceback_dump.txt', 'w+') as dump_file:
        faulthandler.enable(file=dump_file)

        app = PhotonCounter(sys.argv)

        try:
            sys.exit(app.exec_())
        except Exception as e:
            logging.error(str(e))