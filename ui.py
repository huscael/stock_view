from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QVariant
from PyQt5.QtGui import QPen, QBrush, QPalette, QColor
from PyQt5.QtWidgets import QStyle
from tab_ui import TabView
from stock_list_ui import StockListView
from login_ui import LoginWidget
from client_model import ClientModel, LiveCheck

class UiMainWindow(object):
    '''
    used to show application main window
    '''
    def setup_ui(self, MainWindow):
        '''
        ui创建及连接

        Args:
            MainWindow:QMainWindow type, used as application main window
        '''
        #client单例
        self.client_model = ClientModel.getInstance()
        #断线重连
        self.live_check = LiveCheck()
        self.live_check.drop_out.connect(self.show_dialog)
        self.live_check.reconnect_succeed.connect(self.show_dialog)
        self.live_check.reconnect_failed.connect(self.show_dialog)
        self.live_check.start()

        #主窗口
        self.MainWindow = MainWindow
        self.MainWindow.setObjectName("MainWindow")
        self.MainWindow.resize(350, 250)

        #主界面设置为栈堆积，用于切换窗口
        self.stack = QtWidgets.QStackedWidget(self.MainWindow)

        #登陆界面
        self.loginWidget= LoginWidget(self.stack)
        #将登陆界面加入堆积窗口
        self.stack.addWidget(self.loginWidget)

        #建立股票列表界面
        self.list_view = StockListView(self.stack)
        #将股票列表与登陆界面链接,用于实现跳转时加载列表
        self.loginWidget.set_list(self.list_view)
        #将股票列表界面加入堆积窗口
        self.stack.addWidget(self.list_view)
        
        #建立tab界面垂直布局
        self.tab_view = TabView(self.stack)
        #将tab与股票列表链接, 实现双击时加载tab界面
        self.list_view.set_tab(self.tab_view)
        #将tab界面加入堆积窗口
        self.stack.addWidget(self.tab_view)

        #堆积窗口设为中央组件
        self.MainWindow.setCentralWidget(self.stack)

        #顶部栏
        self.menubar = QtWidgets.QMenuBar(self.MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 22))
        self.MainWindow.setMenuBar(self.menubar)

        #设置各组件名称显示
        self.MainWindow.setWindowTitle("狂赌之渊")
        QtCore.QMetaObject.connectSlotsByName(self.MainWindow)

    def show_dialog(self, msg):
        """
        show dialog according to msg

        Args:
            msg: signal message received from live check thread, format:["msg_type", "msg"]
        """
        self.stack.setCurrentWidget(self.loginWidget)
        self.MainWindow.resize(350, 250)
        #centerize view
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        size = self.MainWindow.geometry()
        self.MainWindow.move((screen.width() - size.width()) / 2,
                  (screen.height() - size.height()) / 2)
        msg_box = QtWidgets.QMessageBox(self.MainWindow)
        msg_box.setWindowTitle(msg[0])
        msg_box.setInformativeText(msg[1])
        msg_box.exec_()

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    window = QtWidgets.QMainWindow()
    ui = UiMainWindow()
    ui.setup_ui(window)
    window.show()
    app.exec_()
