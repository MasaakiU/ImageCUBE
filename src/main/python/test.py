from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtCore import Qt, QObject, pyqtSlot
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import (
    QMainWindow, 
    QFileDialog, 
    QWidget, 
    QVBoxLayout, 
    QHBoxLayout,  
    QSpinBox, 
    QDialog, 
    QSizePolicy, 
    QSpacerItem, 
    QDesktopWidget, 
    QMenuBar, 
    QApplication, 
    QLabel,
    QPushButton
    )

import sys

class MyWindow(QWidget):
    def __init__(self):
        super().__init__()
        # self.sub_window = SubWindow(parent=self)

        self.btn = QPushButton("push")
        self.btn.clicked.connect(self.disable_sub2)
        self.btn2 = QPushButton("push2")

        # self.setCentralWidget(self.label)
        layout = QHBoxLayout()
        layout.addWidget(self.btn)
        layout.addWidget(self.btn2)
        self.setLayout(layout)

        # self.setFocusPolicy(Qt.StrongFocus)

    def disable_sub2(self, event=None):
        # self.sub_window.show()
        # # self.sub_window.on_pushButtonSimulate_clicked()
        # self.sub_window.grab_focus()

        # self.btn2.setEnabled(False)
        self.btn2.setEnabled(False)
        QApplication.processEvents()
        # self.btn2.setStyleSheet("QWidget{background-color:red}")



    # def focusInEvent(self, event):
    #     self.label.setText('Got focus')

    # def focusOutEvent(self, event):
    #     self.label.setText('Lost focus')


def main():
    app = QApplication(sys.argv)
    win1 = MyWindow()
    win1.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()