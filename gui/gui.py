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

from qtconsole.qt import QtGui
from qtconsole.rich_jupyter_widget import RichJupyterWidget
from qtconsole.inprocess import QtInProcessKernelManager
from IPython.lib import guisupport

class loggingAdapter(logging.Handler):
    def __init__(self, parent, widget):
        super().__init__()
        self.widget = widget

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)

class ConsoleWidget(RichJupyterWidget):
    def __init__(self, customBanner=None, *args, **kwargs):
        super(ConsoleWidget, self).__init__(*args, **kwargs)

        if customBanner is not None:
            self.banner = customBanner

        self.font_size = 6
        self.kernel_manager = QtInProcessKernelManager()
        self.kernel_manager.start_kernel(show_banner=False)
        self.kernel_manager.kernel.gui = 'qt'
        self.kernel_client = self._kernel_manager.client()
        self.kernel_client.start_channels()

        def stop():
            self.kernel_client.stop_channels()
            self.kernel_manager.shutdown_kernel()
        self.exit_requested.connect(stop)

    def push_vars(self, variableDict):
        """
        Given a dictionary containing name / value pairs, push those variables
        to the Jupyter console widget
        """
        self.kernel_manager.kernel.shell.push(variableDict)

    def clear(self):
        """
        Clears the terminal
        """
        self._control.clear()

        # self.kernel_manager

    def print_text(self, text):
        """
        Prints some plain text to the console
        """
        self._append_plain_text(text)

    def execute_command(self, command):
        """
        Execute a command in the frame of the console widget
        """
        self._execute(command, False)

class PateMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        
        # Create main widget
        mainWidget = QWidget(self)

        textEdit = QPlainTextEdit()
        textEdit.setReadOnly(True)

        logAdapter = loggingAdapter(self, textEdit)
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger().addHandler(logAdapter)
        logging.debug('Log adapter hopefully attached')

        logging.info('Creating JupyterWidget')
        jupyterWidgetConsole = ConsoleWidget()

        vbox = QVBoxLayout()
        vbox.addStretch(1)
        vbox.addWidget(jupyterWidgetConsole)
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