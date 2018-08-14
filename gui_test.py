import sys
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import Qt, Signal, Slot
from matrix_client.client import MatrixClient


class LoginForm(QDialog):
    loggedIn = Signal(object)

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
        self.loggedIn.emit(client)

    def doRegister(self):
        client = MatrixClient(self.homeserver.text())
        client.register_with_password(username=self.username.text(), password=self.password.text())
        client.login_with_password(username=self.username.text(), password=self.password.text())
        self.loggedIn.emit(client)


class RoomItem(QListWidgetItem):
    def __init__(self, room, parent=None):
        super(RoomItem, self).__init__(parent)
        self.room = room
        self.room_id = self.room.room_id
        self.setIcon(QIcon("icon.png"))
        self.setText(self.room.canonical_alias)


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
        print("{}: {}".format(room, message))
        self.messages[room].append(message)

    def roomSelected(self):
        for room in self.selectedItems():
            self.switchRoom.emit(room.room_id)


class MessageItem(QWidget):
    def __init__(self, parent=None):
        super(MessageList, self).__init__(parent)


class MessageList(QFrame):
    def __init__(self, messages, parent=None):
        super(MessageList, self).__init__(parent)
        self.layout = QVBoxLayout()
        for message in messages:
            self.layout.addWidget(QLabel(message['body'], self))
        self.setLayout(self.layout)


class MessageView(QSplitter):
    def __init__(self, parent=None):
        super(MessageView, self).__init__(parent)
        self.messages = {}
        self.activeRoom = ''

        self.messageList = MessageList([])
        self.textEdit = QTextEdit()

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidget(self.messageList)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.setOrientation(Qt.Vertical)
        self.addWidget(self.scrollArea)
        self.addWidget(self.textEdit)

        parent.messageReceived.connect(self.messageReceived)
        parent.switchRoom.connect(self.switchRoom)

    def messageReceived(self, room, message):
        if room not in self.messages:
            self.messages[room] = []
        self.messages[room].append(message)
        if room == self.activeRoom:
            self.messageList.addMessage(message)
        self.switchRoom(room)

    def switchRoom(self, room):
        newMessageList = MessageList(self.messages[room])
        newScrollArea = QScrollArea()
        newScrollArea.setWidget(newMessageList)
        newScrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.replaceWidget(0, newScrollArea)
        
        del self.messageList
        del self.scrollArea
        self.messageList = newMessageList
        self.scrollArea = newScrollArea

class MainPage(QSplitter):
    messageReceived = Signal(str, object)
    switchRoom = Signal(str)

    def __init__(self, parent=None):
        super(MainPage, self).__init__(parent)
        self.rooms = RoomsList(self)
        self.messages = MessageView(self)

        self.loginForm = LoginForm()
        self.loginForm.loggedIn.connect(self.loggedIn)
        self.loginForm.show()

        self.addWidget(self.rooms)
        self.addWidget(self.messages)

        self.client = None

    def loggedIn(self, client):
        self.client = client
        self.client.add_listener(self.eventCallback)
        self.client.start_listener_thread()
        self.loginForm.close()
        for room, obj in self.client.get_rooms().items():
            self.rooms.addItem(obj.room_id, obj)
            for event in obj.events:
                self.eventCallback(event)
        print(client)

    def eventCallback(self, event):
        if 'type' in event and 'room_id' in event and 'content' in event and event['type'] == 'm.room.message':
            print(event['content'])
            self.messageReceived.emit(event['room_id'], event['content'])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainPage = MainPage()
    mainPage.show()
    sys.exit(app.exec_())
