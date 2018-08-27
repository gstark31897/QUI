from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import Qt, Signal, Slot, QSettings


class Header(QWidget):
    leaveRoom = Signal(object)

    def __init__(self, parent=None):
        super(Header, self).__init__(parent)
        self.layout = QHBoxLayout(self)
        self.setMinimumHeight(40)
        self.room = None

        self.roomLabel = QLabel('Room')
        self.layout.addWidget(self.roomLabel)
        self.layout.setAlignment(self.roomLabel, Qt.AlignLeft)

        self.settingsMenuBar = QMenuBar()
        self.settingsMenuBar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        settingsMenu = self.settingsMenuBar.addMenu(QIcon.fromTheme('overflow-menu'), '')
        settingsMenu.addAction('Leave Room').triggered.connect(self.roomLeft)
        self.layout.addWidget(self.settingsMenuBar)
        self.layout.setAlignment(self.settingsMenuBar, Qt.AlignRight)

        self.setLayout(self.layout)

    def switchRoom(self, room):
        self.roomLabel.setText(room.name)
        self.room = room

    def roomLeft(self):
        self.leaveRoom.emit(self.room)

