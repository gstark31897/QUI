from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import Qt, Signal, Slot, QSettings

from matrix_client.client import MatrixClient
from matrix_client.room import Room

import time

from .messageview import MessageView
from .roomlist import RoomList
from .forms.loginform import LoginForm


class MainWindow(QSplitter):
    messageReceived = Signal(object, str, object, float)

    switchRoom = Signal(object)
    roomLeft = Signal(object)
    roomJoined = Signal(object)
    roomUpdated = Signal(str, str, str)

    leaveRoom = Signal(object)
    joinRoom = Signal(str)
    createRoom = Signal(str)


    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.rooms = RoomList(self)
        self.messages = MessageView(self)

        self.addWidget(self.rooms)
        self.addWidget(self.messages)

        self.messages.messageSent.connect(self.rooms.messageSent)

        self.settings = QSettings('Qui', 'Qui')

        # setup signals
        self.resize(int(self.settings.value("width", "960")), int(self.settings.value("height", "667")))
        self.move(int(self.settings.value("xpos", "496")), int(self.settings.value("ypos", "193")))
        self.rooms.switchRoom.connect(self.switchRoom)
        self.rooms.createRoom.connect(self.createRoom)
        self.messages.leaveRoom.connect(self.leaveRoom)
        self.rooms.joinRoom.connect(self.joinRoom)
        self.roomLeft.connect(self.rooms.roomLeft)
        self.roomLeft.connect(self.messages.roomLeft)
        self.roomJoined.connect(self.rooms.roomJoined)
        self.roomJoined.connect(self.messages.roomJoined)
        self.roomUpdated.connect(self.rooms.roomUpdated)
        self.roomUpdated.connect(self.messages.roomUpdated)

    def resizeEvent(self, event):
        super(MainWindow, self).resizeEvent(event)
        self.settings.setValue("width", event.size().width())
        self.settings.setValue("height", event.size().height())

    def moveEvent(self, event):
        super(MainWindow, self).moveEvent(event)
        self.settings.setValue("xpos", event.pos().x())
        self.settings.setValue("ypos", event.pos().y())

    def closeEvent(self, event):
        self.hide()
        #event.accept() TODO make an option to actually close if closed

    def login(self, user):
        self.messages.login(user)

    def receiveMessage(self, room, sender, content, timestamp):
        self.messages.receiveMessage(room, sender, content, timestamp)
        self.rooms.receiveMessage(room, sender, content, timestamp)

    def switchRoom(self, room):
        self.messages.switchRoom(room)

