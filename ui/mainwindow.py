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

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.rooms = RoomList(self)
        self.messages = MessageView(self)

        self.addWidget(self.rooms)
        self.addWidget(self.messages)

        self.messages.messageSent.connect(self.rooms.messageSent)
        self.messages.roomLeft.connect(self.rooms.roomLeft)
        self.messages.roomLeft.connect(self.roomLeft)

        self.client = None
        self.settings = QSettings("Qui", "Qui")
        self.url = self.settings.value("url")
        self.token = self.settings.value("token")
        self.user = self.settings.value("user")
        invalid = self.url is None or self.url == "" or self.token is None or self.token == "" or self.user is None or self.user == ""
        if not invalid:
            #try:
                self.client = MatrixClient(base_url=self.url, token=self.token, user_id=self.user)
                self.postLogin()
            #except:
            #    invalid = True
        if invalid:
            self.loginForm = LoginForm()
            self.loginForm.loggedIn.connect(self.loggedIn)
            self.loginForm.show()

        self.resize(int(self.settings.value("width", "960")), int(self.settings.value("height", "667")))
        self.move(int(self.settings.value("xpos", "496")), int(self.settings.value("ypos", "193")))

    def resizeEvent(self, event):
        super(MainWindow, self).resizeEvent(event)
        self.settings.setValue("width", event.size().width())
        self.settings.setValue("height", event.size().height())

    def moveEvent(self, event):
        super(MainWindow, self).moveEvent(event)
        self.settings.setValue("xpos", event.pos().x())
        self.settings.setValue("ypos", event.pos().y())

    def loggedIn(self, client, baseUrl):
        self.client = client
        self.loginForm.close()
        self.settings.setValue("url", baseUrl)
        self.settings.setValue("token", client.token)
        self.settings.setValue("user", client.user_id)
        self.postLogin()

    def postLogin(self):
        self.messages.userId = self.user
        self.client.add_listener(self.eventCallback)
        self.client.add_presence_listener(self.presenceCallback)
        self.client.add_invite_listener(self.inviteCallback)
        self.client.add_leave_listener(self.leaveCallback)
        self.client.start_listener_thread()
        for room, obj in self.client.get_rooms().items():
            self.rooms.addItem(obj.room_id, obj)
            for event in obj.events:
                self.eventCallback(event)

    def roomLeft(self, room):
        self.client.api.leave_room(room.room_id)

    def eventCallback(self, event):
        if 'type' in event and 'room_id' in event and 'content' in event and event['type'] == 'm.room.message':
            room = Room(self.client, event['room_id'])
            self.messageReceived.emit(room, event['sender'], event['content'], time.time() - event['unsigned']['age'])

    def presenceCallback(self, event):
        print('presence: {}'.format(event))

    def inviteCallback(self, roomId, state):
        print('invite: {} {}'.format(roomId, state))

    def leaveCallback(self, roomId, room):
        print('leave: {} {}'.format(roomId, room))

