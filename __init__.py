from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import Qt, Signal, Slot, QSettings

from matrix_client.client import MatrixClient

from .ui.mainwindow import MainWindow

import sys
import os


class Application(QApplication):
    def __init__(self, *args, **kwargs):
        super(Application, self).__init__(*args, **kwargs)

        self.iconPath = os.path.dirname(__file__)
        self.iconPath = os.path.join(self.iconPath, 'icons/icon.png')

        self.tray = QSystemTrayIcon(QIcon(self.iconPath))
        self.tray.show()
        #self.tray.showMessage('test', 'test')
        self.tray.activated.connect(self.showWindow)

        self.menu = QMenu()
        self.menu.addAction('Quit').triggered.connect(self.quit)
        self.tray.setContextMenu(self.menu)

        self.window = None
        self.showWindow(None)

    def showWindow(self, reason):
        if self.window is None:
            self.window = MainWindow()
            self.window.windowClosed.connect(self.windowClosed)
            self.window.show()
        else:
            self.window.showNormal()

    def windowClosed(self):
        self.window = None

    def quit(self):
        sys.exit(0)

