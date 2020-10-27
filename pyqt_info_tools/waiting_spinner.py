from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel
from PyQt5.QtGui import QColor, QFont, QPainter, QBrush
from PyQt5.QtCore import QMetaObject, Qt, QRunnable, QTimer, QRect, QPoint
from functools import wraps
import math


class QtWaitingSpinner(QWidget):

    # https://stackoverflow.com/questions/52313073/making-an-invisible-layer-in-pyqt-which-covers-the-whole-dialog

    def __init__(self, parent=None,
                 centerOnParent=True,
                 disableParentWhenSpinning=False,
                 modality=Qt.NonModal):

        super().__init__(parent, flags=Qt.Dialog | Qt.FramelessWindowHint)

        self._text = 'Processing ...'
        self._centerOnParent = centerOnParent
        self._disableParentWhenSpinning = disableParentWhenSpinning

        # WAS IN initialize()
        self._color = QColor(Qt.black)
        self._revolutionsPerSecond = 2
        self._currentCounter = 0
        self._isSpinning = False

        self.i = 0
        self.n = 10

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.rotate)
        self.updateSize()
        self.updateTimer()
        self.hide()
        # END initialize()

        widget = QWidget(self)
        self.setWindowModality(modality)
        self.setAttribute(Qt.WA_TranslucentBackground)

        grid = QGridLayout()
        self.setLayout(grid)
        self.setWindowTitle("QtWaitingSpinner Demo")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog | Qt.WindowStaysOnTopHint)

        self.label = QLabel(self)
        self.label.setObjectName("label")
        self.label.setText(self.text)
        self.label.setStyleSheet("color: rgb(255, 255, 255);")
        self.label.setObjectName("label")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFont(QFont('Arial', 12))

        grid.addWidget(widget, *(1, 1))
        grid.addWidget(self.label, *(2, 1))

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value
        self.label.setText(self._text)

    def paintEvent(self, QPaintEvent):
        self.updatePosition()
        painter = QPainter(self)
        rect = QRect(0, 0, self.parent().width(), self.parent().height())
        painter.fillRect(rect, QBrush(QColor(50, 50, 50, 200)))
        painter.setRenderHint(QPainter.Antialiasing, True)

        painter.setPen(Qt.NoPen)

        for i in range(self.n):
            if self.i == i:
                painter.setBrush(QBrush(QColor(100, 100, 255)))
            else:
                painter.setBrush(QBrush(QColor(230, 230, 230)))
            painter.drawEllipse(
                int(self.parent().width() / 2 + 30 * math.cos(2 * math.pi * i / self.n)) - 8,
                int(self.parent().height() / 2 + 30 * math.sin(2 * math.pi * i / self.n)) - 8,
                10, 10)

        painter.end()

    def start(self):
        self.updatePosition()
        self._isSpinning = True
        self.show()

        if self.parentWidget and self._disableParentWhenSpinning:
            self.parentWidget().setEnabled(False)

        if not self._timer.isActive():
            self._timer.start()
            self._currentCounter = 0

    def stop(self):
        self._isSpinning = False
        self.hide()

        if self.parentWidget() and self._disableParentWhenSpinning:
            self.parentWidget().setEnabled(True)

        if self._timer.isActive():
            self._timer.stop()
            self._currentCounter = 0

    def color(self):
        return self._color

    def isSpinning(self):
        return self._isSpinning

    def setColor(self, color=Qt.black):
        self._color = QColor(color)

    def setRevolutionsPerSecond(self, revolutionsPerSecond):
        self._revolutionsPerSecond = revolutionsPerSecond
        self.updateTimer()

    def rotate(self):
        self.i += 1
        if self.i > (self.n - 1):
            self.i = 0
        self.update()

    def updateSize(self):
        # size = (self._innerRadius + self._lineLength) * 2
        # self.setFixedSize(size, size)
        self.setFixedSize(self.parentWidget().size())

    def updateTimer(self):
        self._timer.setInterval(int(1000 / (self.n * self._revolutionsPerSecond)))

    def updatePosition(self):
        if self.parentWidget() and self._centerOnParent:
            parentRect = QRect(self.parentWidget().mapToGlobal(QPoint(0, 0)), self.parentWidget().size())
            # self.move(QtWidgets.QStyle.alignedRect(QtCore.Qt.LeftToRight, QtCore.Qt.AlignCenter, self.size(), parentRect).topLeft())
            self.move(parentRect.x(), parentRect.y())


class RequestRunnable(QRunnable):

    def __init__(self, fcn, dialog, *args, **kwargs):
        super(RequestRunnable, self).__init__()
        self.args = args
        self.kwargs = kwargs
        self.dialog = dialog
        self.fcn = fcn

    def run(self):
        QMetaObject.invokeMethod(self.dialog, "start_process", Qt.QueuedConnection)
        self.fcn(*self.args, **self.kwargs)
        QMetaObject.invokeMethod(self.dialog, "finished_process", Qt.QueuedConnection)


class StartRunnable(QRunnable):

    def __init__(self, dialog, fcn=None, args=(), kwargs={}):
        super(StartRunnable, self).__init__()
        self.w = dialog
        self.fcn = fcn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        print('running start_process')
        QMetaObject.invokeMethod(self.w, "start_process", Qt.QueuedConnection)

        if self.fcn is not None:
            self.fcn(*self.args, **self.kwargs)
            QMetaObject.invokeMethod(self.w, "finished_process", Qt.QueuedConnection)


class StopRunnable(QRunnable):

    def __init__(self, dialog):
        super(StopRunnable, self).__init__()
        self.w = dialog

    def run(self):
        print('running finished_process')
        QMetaObject.invokeMethod(self.w, "finished_process", Qt.QueuedConnection)


def show_waiting(method):
    @wraps(method)
    def _impl(self, *args, **kwargs):
        # QMetaObject.invokeMethod(self.dialog, "start_process", Qt.QueuedConnection)
        self.dialog.start_waiting(fcn=method, args=(self, *args), kwargs=kwargs)
        # method_output = method(self, *args, **kwargs)
        QMetaObject.invokeMethod(self.dialog, "finished_process", Qt.QueuedConnection)
        # return method_output
    return _impl
