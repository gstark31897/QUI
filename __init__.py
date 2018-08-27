from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import Qt, Signal, Slot, QSettings

from matrix_client.client import MatrixClient
from matrix_client.room import Room

from .ui.mainwindow import MainWindow
from .ui.forms.loginform import LoginForm

import sys
import os
import time


class Application(QApplication):
    loggedIn = Signal(str)

    messageReceived = Signal(object, str, object, float)

    roomSwitched = Signal(object)
    roomJoined = Signal(object)
    roomUpdated = Signal(str, str, str)
    roomLeft = Signal(object)
    roomInvited = Signal(object)
    
    def __init__(self, *args, **kwargs):
        super(Application, self).__init__(*args, **kwargs)

        # setup the application name and icon
        self.setApplicationName('Qui')
        self.iconPath = os.path.dirname(__file__)
        self.iconPath = os.path.join(self.iconPath, 'icons/icon.png')
        self.setWindowIcon(QIcon(self.iconPath))

        # setup the tray icon
        self.showNotifications = False
        self.tray = QSystemTrayIcon(QIcon(self.iconPath))
        self.tray.show()
        self.tray.activated.connect(self.showWindow)

        # setup the tray icon menu
        self.menu = QMenu()
        self.menu.addAction('Quit').triggered.connect(self.quit)
        self.tray.setContextMenu(self.menu)

        # setup signals
        self.messageReceived.connect(self.receiveMessage)

        # show the window
        self.window = None
        self.showWindow(None)

        # try loading the login info
        self.client = None
        self.settings = QSettings('Qui', 'Qui')
        self.url = self.settings.value("url")
        self.token = self.settings.value("token")
        self.user = self.settings.value("user")
        invalid = self.url is None or self.url == "" or self.token is None or self.token == "" or self.user is None or self.user == ""
        if not invalid:
            try:
                self.client = MatrixClient(base_url=self.url, token=self.token, user_id=self.user)
                self.postLogin()
            except:
                invalid = True
        # show the login form if we can't login
        if invalid:
            self.loginForm = LoginForm()
            self.loginForm.loggedIn.connect(self.login)
            self.loginForm.show()

    def showWindow(self, reason):
        if self.window is None:
            # make a new window if we don't have one
            self.window = MainWindow()
            # setup signals
            self.loggedIn.connect(self.window.login)
            self.messageReceived.connect(self.window.receiveMessage)
            self.roomLeft.connect(self.window.roomLeft)
            self.roomJoined.connect(self.window.roomJoined)
            self.roomUpdated.connect(self.window.roomUpdated)
            self.window.createRoom.connect(self.createRoom)
            self.window.leaveRoom.connect(self.leaveRoom)
            # show it
            self.window.show()
        else:
            # show it if it's minimized or something
            self.window.showNormal()

    def quit(self):
        sys.exit(0)

    def login(self, client, url):
        self.client = client
        self.settings.setValue('url', url)
        self.url = url
        self.settings.setValue('token', client.token)
        self.token = client.token
        self.settings.setValue('user', client.user_id)
        self.user = client.user_id
        self.postLogin()

    def postLogin(self):
        self.loggedIn.emit(self.user)
        #self.messages.userId = self.user
        self.client.add_listener(self.eventCallback)
        self.client.add_presence_listener(self.presenceCallback)
        self.client.add_invite_listener(self.inviteCallback)
        self.client.add_leave_listener(self.leaveCallback)
        self.client.start_listener_thread()
        for room, obj in self.client.get_rooms().items():
            self.roomJoined.emit(obj)
            for event in obj.events:
                self.eventCallback(event)
        self.showNotifications = True

    def eventCallback(self, event):
        if 'type' in event and 'room_id' in event and 'content' in event and event['type'] == 'm.room.message':
            room = Room(self.client, event['room_id'])
            self.messageReceived.emit(room, event['sender'], event['content'], time.time() - event['unsigned']['age'])
        if 'type' in event and 'room_id' in event and 'content' in event and event['type'] == 'm.room.canonical_alias':
            self.roomUpdated.emit(event['room_id'], 'canonical_alias', event['content']['alias'])

    def presenceCallback(self, event):
        return
        print('presence: {}'.format(event))

    def inviteCallback(self, roomId, state):
        return
        print('invite: {} {}'.format(roomId, state))

    def leaveCallback(self, roomId, room):
        return
        print('leave: {} {}'.format(roomId, room))

    def receiveMessage(self, room, sender, content, timestamp):
        if self.showNotifications:
            if self.window is None or not self.window.isActiveWindow():
                self.tray.showMessage(sender, content['body'])

    def leaveRoom(self, room):
        self.client.api.leave_room(room.room_id)
        self.roomLeft.emit(room)

    def joinRoom(self, room):
        room = self.client.join_room(room.room_id)
        self.roomJoined.emit(room)

    def createRoom(self, roomId):
        room = self.client.create_room(roomId)
        self.roomJoined.emit(room)

