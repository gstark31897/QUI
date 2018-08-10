import sys
from PySide2.QtWidgets import *
from PySide2.QtCore import Qt

class LoginForm(QDialog):
    def __init__(self, parent=None):
        super(LoginForm, self).__init__(parent)
        self.username = QLineEdit("Username")
        self.password = QLineEdit("Password")
        self.password.setEchoMode(QLineEdit.Password)
        self.login = QPushButton("Login")
        self.register = QPushButton("Register")

        layout = QVBoxLayout()
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(self.login)
        layout.addWidget(self.register)

        self.setLayout(layout)
        self.login.clicked.connect(self.doLogin)
        self.register.clicked.connect(self.doRegister)

    def doLogin(self):
        print("logging in")

    def doRegister(self):
        print("registering")

class ChatsList(QListView):
    pass

class MessageList(QFrame):
    def __init__(self, parent=None):
        super(MessageList, self).__init__(parent)
        self.layout = QVBoxLayout()
        self.layout.addWidget(QTextEdit())
        self.layout.addWidget(QTextEdit())
        self.layout.addWidget(QTextEdit())
        self.layout.addWidget(QTextEdit())
        self.layout.addWidget(QTextEdit())
        self.layout.addWidget(QTextEdit())
        self.setLayout(self.layout)

class MessageView(QSplitter):
    def __init__(self, parent=None):
        super(MessageView, self).__init__(parent)
        self.messageList = MessageList()
        self.textEdit = QTextEdit()

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidget(self.messageList)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.setOrientation(Qt.Vertical)
        self.addWidget(self.scrollArea)
        self.addWidget(self.textEdit)

class MainPage(QSplitter):
    def __init__(self, parent=None):
        super(MainPage, self).__init__(parent)
        self.chats = ChatsList()
        self.messages = MessageView()

        self.addWidget(self.chats)
        self.addWidget(self.messages)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainPage = MainPage()
    mainPage.show()
    sys.exit(app.exec_())
