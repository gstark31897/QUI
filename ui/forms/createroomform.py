from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import Qt, Signal, Slot, QSettings


class CreateRoomForm(QDialog):
    createRoom = Signal(str)
    joinRoom = Signal(str)

    def __init__(self, parent=None):
        super(CreateRoomForm, self).__init__(parent)

        self.layout = QVBoxLayout()

        self.roomNameLabel = QLabel('Room Name')
        self.layout.addWidget(self.roomNameLabel)

        self.roomNameEdit = QLineEdit('')
        self.layout.addWidget(self.roomNameEdit)

        self.createButton = QPushButton(QIcon.fromTheme('list-add'), 'Create Room')
        self.layout.addWidget(self.createButton)

        self.joinButton = QPushButton(QIcon.fromTheme('join'), 'Join Room')
        self.layout.addWidget(self.joinButton)

        self.cancelButton = QPushButton(QIcon.fromTheme('dialog-cancel'), 'Cancel')
        self.layout.addWidget(self.cancelButton)

        self.setLayout(self.layout)

        self.createButton.clicked.connect(self.createRoomClicked)
        self.joinButton.clicked.connect(self.joinRoomClicked)
        self.cancelButton.clicked.connect(self.reject)

    def createRoomClicked(self):
        self.createRoom.emit(self.roomNameEdit.text())
        self.roomNameEdit.clear()
        self.accept()

    def joinRoomClicked(self):
        self.joinRoom.emit(self.roomNameEdit.text())
        self.roomNameEdit.clear()
        self.accept()

