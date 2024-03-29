import logging
from io import StringIO
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtGui import QTextCursor, QSyntaxHighlighter, QTextCharFormat, QFont


LEVEL_SYMBOLS = {
    logging.CRITICAL: '[!!!]',
    logging.ERROR: '[!!]',
    logging.WARNING: '[!]',
    logging.INFO: '',
    logging.DEBUG: '',
    logging.NOTSET: '[?]'
}


class QDbgConsole(QTextEdit):
    """
    Usable as a write-to stream: using sys.stdout = <QDbgConsole> object, I can direct all print commands to this widget
    Taken from https://gist.github.com/raphigaziano/4494398 with some modifications
    """

    def __init__(self, parent=None):
        super(QDbgConsole, self).__init__(parent)

        self._buffer = StringIO()

        self.setReadOnly(False)

        self.setStyleSheet("color: white; background-color: rgb(0, 0, 0);")

    def write(self, msg, log=False, level=logging.INFO):
        """Add msg to the console's output, on a new line."""
        self.insertPlainText(msg + "\n")
        # Autoscroll
        self.moveCursor(QTextCursor.End)
        self._buffer.write(msg)
        if log:
            logging.log(level, msg)

    # Most of the file API is provided by the contained StringIO
    # buffer.
    # You can redefine any of those methods here if needed.

    def __getattr__(self, attr):
        """
        Fall back to the buffer object if an attribute can't be found.
        """
        return getattr(self._buffer, attr)


class QDbgHighlight(QSyntaxHighlighter):
    def __init__(self, parent):
        super(QDbgHighlight, self).__init__(parent)

        self.error_format = QTextCharFormat()
        self.error_format.setForeground(Qt.red)
        self.error_format.setFontWeight(QFont.Bold)

        self.warning_format = QTextCharFormat()
        self.warning_format.setForeground(Qt.darkYellow)
        self.warning_format.setFontWeight(QFont.Bold)

    def highlightBlock(self, text: str):
        if text.startswith(LEVEL_SYMBOLS[logging.WARNING]):
            self.setFormat(0, len(text), self.warning_format)
        elif text.startswith(LEVEL_SYMBOLS[logging.CRITICAL]) or text.startswith(LEVEL_SYMBOLS[logging.ERROR]):
            self.setFormat(0, len(text), self.error_format)
