import sys, time, datetime
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import Qt, Signal, Slot, QSettings
from matrix_client.client import MatrixClient
from matrix_client.room import Room
import traceback


class LoginForm(QDialog):
    loggedIn = Signal(object, str)

    def __init__(self, parent=None):
        super(LoginForm, self).__init__(parent)
        self.username = QLineEdit("Username")
        self.password = QLineEdit("Password")
        self.password.setEchoMode(QLineEdit.Password)
        self.homeserver = QLineEdit("Homeserver")
        self.login = QPushButton("Login")
        self.register = QPushButton("Register")

        layout = QVBoxLayout()
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(self.homeserver)
        layout.addWidget(self.login)
        layout.addWidget(self.register)

        self.setLayout(layout)
        self.login.clicked.connect(self.doLogin)
        self.register.clicked.connect(self.doRegister)

    def doLogin(self):
        client = MatrixClient(self.homeserver.text())
        client.login_with_password(username=self.username.text(), password=self.password.text())
        self.loggedIn.emit(client, self.homeserver.text())

    def doRegister(self):
        client = MatrixClient(self.homeserver.text())
        client.register_with_password(username=self.username.text(), password=self.password.text())
        client.login_with_password(username=self.username.text(), password=self.password.text())
        self.loggedIn.emit(client, self.homeserver.text())


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


class RoomsList(QListWidget):
    switchRoom = Signal(object)

    def __init__(self, parent=None):
        super(RoomsList, self).__init__(parent)
        self.rooms = {}
        self.messages = {}

        parent.messageReceived.connect(self.messageReceived)
        self.switchRoom.connect(parent.switchRoom)
        self.itemSelectionChanged.connect(self.roomSelected)

    def addItem(self, name, object):
        self.rooms[name] = RoomItem(object, self)
        super(RoomsList, self).addItem(self.rooms[name])
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


class MessageInput(QPlainTextEdit):
    messageSent = Signal(str)

    def __init__(self, parent=None):
        super(MessageInput, self).__init__(parent)
        self.shouldSend = True
        self.setMinimumHeight(32)
        self.setMaximumHeight(32)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        metrics = QFontMetrics(self.font())
        self.line = metrics.lineSpacing()

    def sendMessage(self):
        text = self.toPlainText()
        if len(text) == 0:
            return
        self.messageSent.emit(text)
        self.clear()
        self.setMaximumHeight(self.line + 14)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return and self.shouldSend:
            self.sendMessage()
            return
        super(MessageInput, self).keyPressEvent(event)
        if event.key() == Qt.Key_Shift:
            self.shouldSend = False
        size = (self.toPlainText().count('\n') + 1) * self.line + 14
        size = min(size, 200)
        self.setMaximumHeight(size)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Shift:
            self.shouldSend = True


class MessageViewFooter(QWidget):
    messageSent = Signal(str)

    def __init__(self, parent=None):
        super(MessageViewFooter, self).__init__(parent)
        self.layout = QHBoxLayout(self)
        self.setMinimumHeight(40)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)

        self.attachmentButton = QPushButton(QIcon.fromTheme('mail-attachment'), '', self)
        self.attachmentButton.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.attachmentButton.setMaximumWidth(32)
        self.layout.addWidget(self.attachmentButton)
        self.layout.setAlignment(self.attachmentButton, Qt.AlignBottom)

        self.messageInput = MessageInput(self)
        self.layout.addWidget(self.messageInput)
        self.layout.setAlignment(self.messageInput, Qt.AlignBottom)

        self.sendButton = QPushButton(QIcon.fromTheme('document-send'), '', self)
        self.sendButton.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.sendButton.setMaximumWidth(32)
        self.layout.addWidget(self.sendButton)
        self.layout.setAlignment(self.sendButton, Qt.AlignBottom)

        self.setLayout(self.layout)

        self.messageInput.messageSent.connect(self.messageSent)
        self.sendButton.clicked.connect(self.messageInput.sendMessage)


class MessageViewHeader(QWidget):
    roomLeft = Signal(object)

    def __init__(self, parent=None):
        super(MessageViewHeader, self).__init__(parent)
        self.layout = QHBoxLayout(self)
        self.setMinimumHeight(40)
        self.room = None

        self.roomLabel = QLabel('Room')
        self.layout.addWidget(self.roomLabel)
        self.layout.setAlignment(self.roomLabel, Qt.AlignLeft)

        self.settingsMenuBar = QMenuBar()
        self.settingsMenuBar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        settingsMenu = self.settingsMenuBar.addMenu(QIcon.fromTheme('overflow-menu'), '')
        settingsMenu.addAction('Leave Room').triggered.connect(self.leaveRoom)
        self.layout.addWidget(self.settingsMenuBar)
        self.layout.setAlignment(self.settingsMenuBar, Qt.AlignRight)

        self.setLayout(self.layout)

    def switchRoom(self, room):
        self.roomLabel.setText(room.name)
        self.room = room

    def leaveRoom(self):
        self.roomLeft.emit(self.room)


class MessageView(QWidget):
    messageSent = Signal(str)
    roomLeft = Signal(object)

    def __init__(self, parent=None):
        super(MessageView, self).__init__(parent)
        self.messages = {}
        self.activeRoom = None
        self.userId = ''

        self.layout = QVBoxLayout(self)

        self.roomHeader = MessageViewHeader()

        self.messageList = MessageList(self.userId, [], self)
        self.messageList.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)

        self.messageInput = MessageViewFooter()

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidget(self.messageList)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)

        self.layout.addWidget(self.roomHeader)
        self.layout.addWidget(self.scrollArea)
        self.layout.addWidget(self.messageInput)

        self.setLayout(self.layout)

        parent.messageReceived.connect(self.messageReceived)
        self.roomHeader.roomLeft.connect(self.roomLeft)
        self.roomHeader.roomLeft.connect(self.leaveRoom)
        self.messageInput.messageSent.connect(self.messageSent)
        parent.switchRoom.connect(self.switchRoom)

    def messageReceived(self, room, sender, message, timestamp):
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
        self.roomHeader.switchRoom(room)

        self.messageList.deleteLater()
        self.scrollArea.deleteLater()
        self.messageList = newMessageList
        self.scrollArea = newScrollArea

    def leaveRoom(self, room):
        if room.room_id in self.messages:
            self.messages[room.room_id]


class MainPage(QSplitter):
    messageReceived = Signal(object, str, object, float)
    switchRoom = Signal(object)

    def __init__(self, parent=None):
        super(MainPage, self).__init__(parent)
        self.rooms = RoomsList(self)
        self.messages = MessageView(self)

        # TODO turn this on some day
        # self.tray = QSystemTrayIcon(QIcon('icon.png'))
        # self.tray.show()
        # self.tray.showMessage('test', 'test')

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
            try:
                self.client = MatrixClient(base_url=self.url, token=self.token, user_id=self.user)
                self.postLogin()
            except:
                invalid = True
        if invalid:
            self.loginForm = LoginForm()
            self.loginForm.loggedIn.connect(self.loggedIn)
            self.loginForm.show()

        self.resize(int(self.settings.value("width", "960")), int(self.settings.value("height", "667")))
        self.move(int(self.settings.value("xpos", "496")), int(self.settings.value("ypos", "193")))

    def resizeEvent(self, event):
        super(MainPage, self).resizeEvent(event)
        self.settings.setValue("width", event.size().width())
        self.settings.setValue("height", event.size().height())

    def moveEvent(self, event):
        super(MainPage, self).moveEvent(event)
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



if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainPage = MainPage()
    mainPage.show()
    sys.exit(app.exec_())
