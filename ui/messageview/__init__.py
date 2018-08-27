from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import Qt, Signal, Slot, QSettings

import datetime

from .header import Header
from .footer import Footer


class MessageItem(QFrame):
    def __init__(self, sender, message, timestamp, parent=None):
        super(MessageItem, self).__init__(parent)
        self.layout = QVBoxLayout()

        self.userId = sender

        self.sender = QLabel(sender, self)
        self.layout.addWidget(self.sender)
        self.layout.setAlignment(self.sender, Qt.AlignLeft)

        self.body = QLabel(message['body'], self)
        self.layout.addWidget(self.body)
        self.layout.setAlignment(self.sender, Qt.AlignLeft)

        self.timestamp = QLabel(datetime.datetime.fromtimestamp(int(timestamp)).strftime('%H:%M:%S'), self)
        self.layout.addWidget(self.timestamp)
        self.layout.setAlignment(self.timestamp, Qt.AlignRight)

        self.layout.setContentsMargins(8, 4, 8, 4)
        self.layout.setSpacing(0)

        self.setFrameStyle(QFrame.StyledPanel)
        self.setStyleSheet('border-radius:4px;background:white;');
        self.setLayout(self.layout)


class MessageList(QFrame):
    def __init__(self, userId, messages, parent=None):
        super(MessageList, self).__init__(parent)
        self.layout = QVBoxLayout()
        for message in messages:
            newItem = MessageItem(*message, self)
            self.layout.addWidget(newItem)
            if newItem.userId == userId:
                self.layout.setAlignment(newItem, Qt.AlignRight)
            else:
                self.layout.setAlignment(newItem, Qt.AlignLeft)
        self.setLayout(self.layout)


class MessageView(QWidget):
    messageSent = Signal(str)
    roomLeft = Signal(object)

    def __init__(self, parent=None):
        super(MessageView, self).__init__(parent)
        self.messages = {}
        self.activeRoom = None
        self.userId = ''

        self.layout = QVBoxLayout(self)

        self.header = Header()

        self.messageList = MessageList(self.userId, [], self)
        self.messageList.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)

        self.messageInput = Footer()

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidget(self.messageList)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)

        self.layout.addWidget(self.header)
        self.layout.addWidget(self.scrollArea)
        self.layout.addWidget(self.messageInput)

        self.setLayout(self.layout)

        self.header.roomLeft.connect(self.roomLeft)
        self.header.roomLeft.connect(self.leaveRoom)
        self.messageInput.messageSent.connect(self.messageSent)

    def login(self, userId):
        self.userId = userId

    def receiveMessage(self, room, sender, message, timestamp):
        if room.room_id not in self.messages:
            self.messages[room.room_id] = []
        self.messages[room.room_id].append((sender, message, timestamp))
        if self.activeRoom is not None and room.room_id == self.activeRoom.room_id:
            self.switchRoom(room)

    def switchRoom(self, room):
        newMessageList = MessageList(self.userId, self.messages[room.room_id], self)
        newScrollArea = QScrollArea()
        newScrollArea.setWidget(newMessageList)
        newScrollArea.setWidgetResizable(True)
        newScrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        newScrollArea.verticalScrollBar().setValue(newScrollArea.verticalScrollBar().maximum())
        self.layout.replaceWidget(self.scrollArea, newScrollArea)
        self.activeRoom = room
        self.header.switchRoom(room)

        self.messageList.deleteLater()
        self.scrollArea.deleteLater()
        self.messageList = newMessageList
        self.scrollArea = newScrollArea

    def leaveRoom(self, room):
        if room.room_id in self.messages:
            self.messages[room.room_id]

    def joinRoom(self, room):
        self.messages[room.room_id] = []
        self.switchRoom(room)

