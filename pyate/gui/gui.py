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
    QDockWidget,
    QFileDialog,
    QHBoxLayout,
    QPlainTextEdit,
    QStyle,
    QTextEdit,
    QTreeView,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget)
from PyQt5.QtGui import (
    QFont,
    QIcon,
    QStandardItem,
    QStandardItemModel)
from PyQt5.QtCore import (
    Qt,
    QCoreApplication)
# from PyQt5 import QtCore

from qtconsole.qt import QtGui
from qtconsole.rich_jupyter_widget import RichJupyterWidget
from qtconsole.inprocess import QtInProcessKernelManager
from IPython.lib import guisupport

import tables

class loggingAdapter(logging.Handler):
    def __init__(self, parent, widget):
        super().__init__()
        self.widget = widget

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)

class ConsoleWidget(RichJupyterWidget):
    def __init__(self, *args, customBanner=None,  myWidget=None, **kwargs):
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
        
        self.kernel_manager.kernel.shell.push({'widget':self,'myWidget':myWidget})

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

class h5TreeWidget(QTreeView):
    def __init__(self):
        super().__init__()

        self.mymodel = QStandardItemModel()
        self.mymodel.setHorizontalHeaderLabels([self.tr("Object")])
        self.setModel(self.mymodel)
        
        self.h5filename = None
        
    def seth5filename(self, fname):
        logging.debug('h5 filename set')
        self.h5filename = fname
        self.updateTree()
        
        
    def updateTree(self):
        logging.debug('Updating tree')
        h5file = tables.open_file(self.h5filename, mode='r')
        
        self.walkTree(self.mymodel, h5file.root)
        
        h5file.close()
        
        #self.setModel(self.mymodel)
        
    def walkTree(self, parent, h5item):
        try:
            if h5item._c_classid == 'GROUP':
                for g in h5item._f_list_nodes():
                    name = g._c_classid + ': ' + g._v_name
                    logging.debug(name)
                    item = QStandardItem(name)
                    parent.appendRow(item)
    
                    self.walkTree(item, g)
            else:
                pass
                
        except:
            logging.debug('Leaf!')
            
            
        

class PateMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        # Construct the menubar
        bar = self.menuBar()
        file = bar.addMenu('&File')
        openAction = QAction('&Open', self)
        #openAction.triggered.connect(self.processTrigger) 
        file.addAction(openAction)
        file.triggered[QAction].connect(self.processTrigger)

        ### Tree Dock

        # Create Tree Widget & Populate with data        
        self.tree1View = h5TreeWidget()
        #self.model = QStandardItemModel()
        #self.model.setHorizontalHeaderLabels([self.tr("Object")])
        ##self.addItems(self.model, data)
        #self.tree1View.setModel(self.model)

        # Create dock for tree1
        self.dockTree1 = QDockWidget('Tree', self)
        self.dockTree1.setWidget(self.tree1View)
        self.dockTree1.setFloating(False)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dockTree1)

        ### Log Dock
        
        # Create Log Widget
        self.logTextEdit = QPlainTextEdit()
        self.logTextEdit.setReadOnly(True)
        logAdapter = loggingAdapter(self, self.logTextEdit)
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger().addHandler(logAdapter)
        logging.debug('Log adapter hopefully attached')
        
        # Create dock for log window
        self.dockLog = QDockWidget('Log', self)
        self.dockLog.setWidget(self.logTextEdit)
        self.dockLog.setFloating(False)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dockLog)

        ### Jupyter Dock
        
        # Create textEdit linked to Jupyter widget
        logging.info('Creating textEdit for Jupyter')
        textEditJupyter = QPlainTextEdit()
        textEditJupyter.insertPlainText('Type the following to access content:\nmyWidget.toPlainText()')
        
        # Create the docs
        self.dockJupyterEdit = QDockWidget('textEdit for Jupyter', self)
        self.dockJupyterEdit.setWidget(textEditJupyter)
        self.dockJupyterEdit.setFloating(False)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dockJupyterEdit)
        
        # Create Jupyter widget
        logging.info('Creating JupyterWidget')
        jupyterWidgetConsole = ConsoleWidget(myWidget=textEditJupyter)

        # Create the docs
        self.dockJupyter = QDockWidget('Jupyter console', self)
        self.dockJupyter.setWidget(jupyterWidgetConsole)
        self.dockJupyter.setFloating(False)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dockJupyter)

        # Now we construct the central Widget & it's layout
        mainWidget = QWidget(self)
                
        # Create & assign layout for mainWidget
        layout = QHBoxLayout()
        mainWidget.setLayout(layout)

        # Tabbify overlapping docks
        self.tabifyDockWidget(self.dockLog, self.dockJupyter)

        # Set mainWidget to be central widget
        self.setCentralWidget(mainWidget)
        self.setGeometry(300, 300, 800, 450)
        self.setWindowTitle('PyATE')
        self.show()

    def processTrigger(self, q):
        try:
            message = q.text()+" is triggered"
            logging.debug(message)
            print(message)
            
            if q.text() == '&Open':
                fname = QFileDialog.getOpenFileName(self, 'Open file', 
                                                    '','HDF5 Files (*.h5)')
                logging.info(fname)
                self.tree1View.seth5filename(fname[0])
                
            
        except:
            logging.error('processTrigger(): Exception!')
            logging.error(sys.exc_info()[0])
        

def bleh(self):
    logging.debug('Button pressed')

def main():
    app = QApplication(sys.argv)
    guiMain = PateMainWindow()
    try:
        retval = app.exec_()
    except:     # This doesn't seem to actually work.
        print('Uncaught Exception')
        sys.exit(1)
    sys.exit(retval)

if __name__ == '__main__':
    main()