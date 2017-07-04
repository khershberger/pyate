'''
Created on Jul 4, 2017

Created on Sat Mar 11 09:29:32 2017

Tutorial from:
    http://zetcode.com/gui/pyqt5/menustoolbars/

@author: kyleh


'''

import logging
import sys
from PyQt5.QtWidgets import (
    QMainWindow,
    QAction,
    qApp,
    QApplication,
    QPlainTextEdit,
    QStyle,
    QTextEdit,
    QVBoxLayout,
    QWidget)
from PyQt5.QtGui import (QIcon, QFont)
from PyQt5.QtCore import QCoreApplication
# from PyQt5 import QtCore

class loggingAdapter(logging.Handler):
    def __init__(self, parent, widget):
        super().__init__()
        self.widget = widget

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)


class PateMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        # Create main widget
        mainWidget = QWidget(self)

        textEdit = QPlainTextEdit()
        textEdit.setReadOnly(True)

        logAdapter = loggingAdapter(self, textEdit)
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger().addHandler(logAdapter)

        logging.debug('Log adapter hopefully attached')

        vbox = QVBoxLayout()
        vbox.addStretch(1)
        vbox.addWidget(textEdit)
        mainWidget.setLayout(vbox)

        self.setCentralWidget(mainWidget)

        exitAction = QAction(self.style().standardIcon(QStyle.SP_DialogCloseButton),
                             '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(qApp.quit)
        #exitAction.triggered.connect(self.bleh)

        self.statusBar()

        # menubar = self.menuBar()
        self.fileMenu = self.menuBar().addMenu('&File')
        self.fileMenu.addAction(exitAction)

        self.toolbar = self.addToolBar('Exit')
        self.toolbar.addAction(exitAction)

        self.setGeometry(300, 300, 800, 450)
        self.setWindowTitle('PyATE')
        self.show()

def bleh(self):
    logging.debug('Button pressed')

def main():
    app = QApplication(sys.argv)
    guiMain = PateMainWindow()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()