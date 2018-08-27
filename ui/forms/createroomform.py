from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import Qt, Signal, Slot, QSettings


class CreateRoomForm(QDialog):
    loggedIn = Signal(object, str)

    def __init__(self, parent=None):
        super(CreateRoomForm, self).__init__(parent)

        self.layout = QVBoxLayout()

        self.roomNameLabel = QLabel('Room Name')
        self.layout.addWidget(self.roomNameLabel)

        self.roomNameEdit = QLineEdit('')
        self.layout.addWidget(self.roomNameEdit)

        self.createButton = QPushButton(QIcon.fromTheme('list-add'), 'Create Room')
        self.layout.addWidget(self.createButton)

        self.cancelButton = QPushButton(QIcon.fromTheme('dialog-cancel'), 'Cancel')
        self.layout.addWidget(self.cancelButton)

        self.setLayout(self.layout)

        self.createButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)

    def roomName(self):
        return self.roomNameEdit.text()

