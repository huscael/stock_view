from PyQt5 import QtWidgets, QtCore, QtGui
from ui import UiMainWindow

if __name__ == "__main__" :
    app = QtWidgets.QApplication([])
    window = QtWidgets.QMainWindow()
    ui = UiMainWindow()
    ui.setup_ui(window)
    window.show()
    app.exec_()