from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import Qt, Signal, Slot, QSettings


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


class Footer(QWidget):
    messageSent = Signal(str)

    def __init__(self, parent=None):
        super(Footer, self).__init__(parent)
        self.layout = QHBoxLayout(self)
        self.setMinimumHeight(40)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)

        self.attachmentButton = QPushButton(QIcon.fromTheme('mail-attachment'), '', self)
        self.attachmentButton.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.attachmentButton.setMaximumWidth(32)
        #self.attachmentButton.setFlat(True)
        self.layout.addWidget(self.attachmentButton)
        self.layout.setAlignment(self.attachmentButton, Qt.AlignBottom)

        self.messageInput = MessageInput(self)
        self.layout.addWidget(self.messageInput)
        self.layout.setAlignment(self.messageInput, Qt.AlignBottom)

        self.sendButton = QPushButton(QIcon.fromTheme('document-send'), '', self)
        self.sendButton.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.sendButton.setMaximumWidth(32)
        #self.sendButton.setFlat(True)
        self.layout.addWidget(self.sendButton)
        self.layout.setAlignment(self.sendButton, Qt.AlignBottom)

        self.setLayout(self.layout)

        self.messageInput.messageSent.connect(self.messageSent)
        self.sendButton.clicked.connect(self.messageInput.sendMessage)

