import sys, time, datetime
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import Qt, Signal, Slot, QSettings
from matrix_client.client import MatrixClient
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
        self.setIcon(QIcon("icon.png"))
        self.setText(self.room.canonical_alias)

    def messageSent(self, message):
        self.room.send_text(message)


class RoomsList(QListWidget):
    switchRoom = Signal(str)

    def __init__(self, parent=None):
        super(RoomsList, self).__init__(parent)
        self.messages = {}

        parent.messageReceived.connect(self.messageReceived)
        self.switchRoom.connect(parent.switchRoom)
        self.itemSelectionChanged.connect(self.roomSelected)

    def addItem(self, name, obj):
        super(RoomsList, self).addItem(RoomItem(obj, self))
        self.messages[name] = []

    def messageReceived(self, room, message):
        self.messages[room].append(message)

    def roomSelected(self):
        for room in self.selectedItems():
            self.switchRoom.emit(room.room_id)

    def messageSent(self, message):
        for room in self.selectedItems():
            room.messageSent(message)


class MessageItem(QWidget):
    def __init__(self, sender, message, timestamp, parent=None):
        super(MessageItem, self).__init__(parent)
        self.layout = QVBoxLayout()

        if sender is not None:
            self.sender = QLabel(sender, self)
        self.body = QLabel(message['body'], self)
        self.timestamp = QLabel(datetime.datetime.fromtimestamp(int(timestamp)).strftime('%H:%M:%S'), self)

        self.layout.addWidget(self.sender)
        self.layout.addWidget(self.body)
        self.layout.addWidget(self.timestamp)

        self.setLayout(self.layout)
        self.setStyleSheet('background-color:white;');


class MessageList(QFrame):
    def __init__(self, messages, parent=None):
        super(MessageList, self).__init__(parent)
        self.layout = QVBoxLayout()
        for message in messages:
            self.layout.addWidget(MessageItem(*message, self))
        self.setLayout(self.layout)


class MessageInput(QPlainTextEdit):
    messageSent = Signal(str)

    def __init__(self, parent=None):
        super(MessageInput, self).__init__(parent)
        self.shouldSend = True

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return and self.shouldSend:
            text = self.toPlainText()
            if len(text) == 0:
                return
            self.messageSent.emit(text)
            self.clear()
            return
        super(MessageInput, self).keyPressEvent(event)
        if event.key() == Qt.Key_Shift:
            self.shouldSend = False

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Shift:
            self.shouldSend = True


class MessageView(QSplitter):
    messageSent = Signal(str)

    def __init__(self, parent=None):
        super(MessageView, self).__init__(parent)
        self.messages = {}
        self.activeRoom = ''
        self.userId = ''

        self.messageList = MessageList([], self)
        self.messageInput = MessageInput()

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidget(self.messageList)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.setOrientation(Qt.Vertical)
        self.addWidget(self.scrollArea)
        self.addWidget(self.messageInput)

        parent.messageReceived.connect(self.messageReceived)
        self.messageInput.messageSent.connect(self.messageSent)
        parent.switchRoom.connect(self.switchRoom)

    def messageReceived(self, room, sender, message, timestamp):
        if room not in self.messages:
            self.messages[room] = []
        self.messages[room].append((sender, message, timestamp))
        if room == self.activeRoom:
            self.switchRoom(room)

    def switchRoom(self, room, *args):
        newMessageList = MessageList(self.messages[room], self)
        newScrollArea = QScrollArea()
        newScrollArea.setWidget(newMessageList)
        newScrollArea.setWidgetResizable(True)
        newScrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        newScrollArea.verticalScrollBar().setValue(newScrollArea.verticalScrollBar().maximum())
        self.replaceWidget(0, newScrollArea)
        self.activeRoom = room

        self.messageList.deleteLater()
        self.scrollArea.deleteLater()
        self.messageList = newMessageList
        self.scrollArea = newScrollArea

class MainPage(QSplitter):
    messageReceived = Signal(str, str, object, float)
    switchRoom = Signal(str)

    def __init__(self, parent=None):
        super(MainPage, self).__init__(parent)
        self.rooms = RoomsList(self)
        self.messages = MessageView(self)

        self.addWidget(self.rooms)
        self.addWidget(self.messages)

        self.messages.messageSent.connect(self.rooms.messageSent)

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
        self.client.start_listener_thread()
        for room, obj in self.client.get_rooms().items():
            self.rooms.addItem(obj.room_id, obj)
            for event in obj.events:
                self.eventCallback(event)

    def eventCallback(self, event):
        print(event)
        if 'type' in event and 'room_id' in event and 'content' in event and event['type'] == 'm.room.message':
            self.messageReceived.emit(event['room_id'], event['sender'], event['content'], time.time() - event['unsigned']['age'])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainPage = MainPage()
    mainPage.show()
    sys.exit(app.exec_())
