from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import pyqtSignal

from threading import Timer


class ObjectLabel(QLabel):
    clicked = pyqtSignal()

    def __init__(self, *args, **kwargs):
        QLabel.__init__(self, *args, **kwargs)
        self._no_of_clicks = 0
        self.instance = None

    def mousePressEvent(self, event):
        self._no_of_clicks = self._no_of_clicks + 1
        timer = Timer(0.3, self.reset_clicks)
        if self._no_of_clicks > 1:
            double_clicked = True
        else:
            double_clicked = False
        timer.start()
        if double_clicked:
            self.clicked.emit()
        QLabel.mousePressEvent(self, event)

    def reset_clicks(self):
        self._no_of_clicks = 0