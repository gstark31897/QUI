from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import Qt, Signal, Slot, QSettings, QCoreApplication

from .footer import Footer


class RoomItem(QListWidgetItem):
    def __init__(self, room, parent=None):
        super(RoomItem, self).__init__(parent)
        self.room = room
        self.room_id = self.room.room_id
        if self.room.name is None:
            self.name = self.room.canonical_alias
        else:
            self.name = self.room.name
        self.setIcon(QIcon("icon.png"))
        self.setText(self.room.canonical_alias)

    def messageSent(self, message):
        self.room.send_text(message)

    def leave(self):
        self.room.leave_room(self.room_id)

    def update(self, key, value):
        if key == 'canonical_alias':
            self.canonical_alias = value
            self.setText(self.room.canonical_alias)


class RoomList(QWidget):
    switchRoom = Signal(object)

    roomCreated = Signal(object)
    createRoom = Signal(str)

    def __init__(self, parent=None):
        super(RoomList, self).__init__(parent)
        self.rooms = {}

        self.layout = QVBoxLayout(self)

        self.list = QListWidget(self)
        self.list.setSortingEnabled(True)
        self.layout.addWidget(self.list)

        self.footer = Footer(self)
        self.layout.addWidget(self.footer)

        self.setLayout(self.layout)

        self.list.itemSelectionChanged.connect(self.roomSelected)
        self.footer.createRoom.connect(self.createRoom)

    def addItem(self, room):
        newRoom = RoomItem(room, self.list)
        self.rooms[newRoom.room_id] = newRoom
        self.list.addItem(self.rooms[newRoom.room_id])

    def selectedItems(self):
        return self.list.selectedItems()

    def roomSelected(self):
        for room in self.selectedItems():
            self.switchRoom.emit(room)

    def messageSent(self, message):
        for room in self.list.selectedItems():
            room.messageSent(message)

    def receiveMessage(self, room, sender, content, timestamp):
        pass # TODO show a notification

    def roomLeft(self, room):
        self.list.takeItem(self.list.row(self.rooms[room.room_id]))
        del self.rooms[room.room_id]

    def roomJoined(self, room):
        self.addItem(room)

    def roomUpdated(self, roomId, key, value):
        if roomId in self.rooms:
            self.rooms[roomId].update(key, value)
            self.repaint()

