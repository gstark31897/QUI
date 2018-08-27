from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import Qt, Signal, Slot

from ..forms.createroomform import CreateRoomForm


class Footer(QWidget):
    createRoom = Signal(str)

    def __init__(self, parent=None):
        super(Footer, self).__init__(parent)
        self.layout = QHBoxLayout(self)
        self.setMinimumHeight(40)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)

        self.createRoomForm = CreateRoomForm(self)
        self.createRoomForm.accepted.connect(self.roomCreateAccepted)

        self.createRoomButton = QPushButton(QIcon.fromTheme('list-add'), '')
        self.createRoomButton.setFlat(True)
        self.createRoomButton.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.createRoomButton.clicked.connect(self.createRoomForm.exec)
        self.layout.addWidget(self.createRoomButton)
        self.layout.setAlignment(self.createRoomButton, Qt.AlignBottom)

        self.contactsButton = QPushButton(QIcon.fromTheme('user'), '')
        self.contactsButton.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.contactsButton.setFlat(True)
        self.layout.addWidget(self.contactsButton)
        self.layout.setAlignment(self.contactsButton, Qt.AlignBottom)

        self.settingsButton = QPushButton(QIcon.fromTheme('configure'), '')
        self.settingsButton.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.settingsButton.setFlat(True)
        self.layout.addWidget(self.settingsButton)
        self.layout.setAlignment(self.settingsButton, Qt.AlignBottom)

        self.setLayout(self.layout)

    def roomCreateAccepted(self):
        self.createRoom.emit(self.createRoomForm.roomName())

