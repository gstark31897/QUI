import sys, time, datetime
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

    def messageSent(self, message):
        self.room.send_text(message)
        print(message)


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
            print(message)
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

        self.messageList = MessageList([])
        self.messageInput = MessageInput()

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidget(self.messageList)
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
        self.switchRoom(room)

    def switchRoom(self, room):
        newMessageList = MessageList(self.messages[room])
        newScrollArea = QScrollArea()
        newScrollArea.setWidget(newMessageList)
        newScrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        newScrollArea.verticalScrollBar().setValue(newScrollArea.verticalScrollBar().maximum())
        self.replaceWidget(0, newScrollArea)
        
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

        self.loginForm = LoginForm()
        self.loginForm.loggedIn.connect(self.loggedIn)
        self.loginForm.show()

        self.addWidget(self.rooms)
        self.addWidget(self.messages)

        self.client = None
        self.messages.messageSent.connect(self.rooms.messageSent)

    def loggedIn(self, client):
        self.client = client
        self.client.add_listener(self.eventCallback)
        self.client.start_listener_thread()
        self.loginForm.close()
        for room, obj in self.client.get_rooms().items():
            self.rooms.addItem(obj.room_id, obj)
            for event in obj.events:
                self.eventCallback(event)

    def eventCallback(self, event):
        if 'type' in event and 'room_id' in event and 'content' in event and event['type'] == 'm.room.message':
            print(event)
            self.messageReceived.emit(event['room_id'], event['sender'], event['content'], time.time() - event['unsigned']['age'])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainPage = MainPage()
    mainPage.show()
    sys.exit(app.exec_())
