from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import Qt, Signal, Slot, QSettings


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


class RoomList(QListWidget):
    switchRoom = Signal(object)

    def __init__(self, parent=None):
        super(RoomList, self).__init__(parent)
        self.rooms = {}
        self.messages = {}

        parent.messageReceived.connect(self.messageReceived)
        self.switchRoom.connect(parent.switchRoom)
        self.itemSelectionChanged.connect(self.roomSelected)

    def addItem(self, name, object):
        self.rooms[name] = RoomItem(object, self)
        super(RoomList, self).addItem(self.rooms[name])
        self.messages[name] = []

    def messageReceived(self, room, message):
        self.messages[room.room_id].append(message)

    def roomSelected(self):
        for room in self.selectedItems():
            self.switchRoom.emit(room)

    def messageSent(self, message):
        for room in self.selectedItems():
            room.messageSent(message)

    def roomLeft(self, room):
        self.takeItem(self.row(self.rooms[room.room_id]))
        del self.rooms[room.room_id]
        del self.messages[room.room_id]

