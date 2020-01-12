from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import Qt
from my_logger import MyLogger
import time
from client_model import ClientModel

class LoginWidget(QtWidgets.QWidget):
    '''
    inherit QWidget, using for displaying login view
    '''
    def __init__(self, parent = None):
        '''
        initialize object

        Args:
            parent: parent widget
        '''
        super(LoginWidget, self).__init__(parent)

        self.client_model = ClientModel.getInstance()

        #self.logger = MyLogger().get_logger()

        #self.setGeometry(QtCore.QRect(80, 40, 631, 471))

        #垂直布局
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        #将图片插入垂直布局
        self.pic_label = QtWidgets.QLabel(self)
        pic = QtGui.QPixmap("login_pic.jpg")
        self.pic_label.setPixmap(pic)
        self.pic_label.setScaledContents(True)
        self.main_layout.addWidget(self.pic_label)

        #登陆网格布局
        self.grid_layout = QtWidgets.QGridLayout()
        self.grid_layout.setVerticalSpacing(0)
        self.grid_layout.setContentsMargins(10, -1, 10, -1)
        self.grid_layout.setVerticalSpacing(10)
        self.user_name_edit= QtWidgets.QLineEdit(self) #账号输入行
        self.user_name_edit.setObjectName("user_name_edit")
        self.grid_layout.addWidget(self.user_name_edit, 0, 1, 1, 1)
        self.label_2 = QtWidgets.QLabel(self) #账号标签
        self.label_2.setObjectName("label_2")
        self.grid_layout.addWidget(self.label_2, 1, 0, 1, 1)
        self.label = QtWidgets.QLabel(self) #密码标签
        self.label.setObjectName("label")
        self.grid_layout.addWidget(self.label, 0, 0, 1, 1)
        self.password_edit= QtWidgets.QLineEdit(self) #密码输入行
        self.password_edit.setObjectName("password_edit")
        self.password_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.grid_layout.addWidget(self.password_edit, 1, 1, 1, 1)
        #将登陆网格加入垂直布局
        self.login_groupbox = QtWidgets.QGroupBox(self)
        self.login_groupbox.setLayout(self.grid_layout)
        self.main_layout.addWidget(self.login_groupbox)
        #将登陆按钮插入垂直布局
        self.login_btn = QtWidgets.QPushButton(self)
        self.login_btn.setObjectName("login_btn")
        self.main_layout.addWidget(self.login_btn)
        #登陆按钮按下事件连接
        self.login_btn.clicked.connect(self.loginBtnClicked)
        #设置显示文本
        self.label_2.setText("密码")
        self.label.setText("用户名")
        self.login_btn.setText("登陆")

    def set_list(self, list_view):
        '''
        obtain list_view widget, intending to realize lazy load stock list

        Args:
            list_view: StockListView object
        '''
        self.stock_list_view = list_view

    def loginBtnClicked(self):
        '''
        login event, suppposed to connect to login_btn

        Query server to check user's identification throught client_model.
        
        Jump to stock list view if successfully logged in, else pop error dialog and retry.
        '''
        user_name = self.user_name_edit.text()
        password = self.password_edit.text()
        #self.logger.info("login button clicked...")
        #判断是否登陆成功，与服务器通信
        if self.client_model.login(user_name, password):
            #加载股票列表数据
            self.stock_list_view.list_view.startLoader()
            #切换视图
            self.parentWidget().setCurrentIndex(1)

            self.parentWidget().parentWidget().resize(1440, 900)
            screen = QtWidgets.QDesktopWidget().screenGeometry()
            size = self.parentWidget().parentWidget().geometry()
            self.parentWidget().parentWidget().move((screen.width() - size.width()) / 2,
                    (screen.height() - size.height()) / 2)
            
            #self.logger.info("successfully login: user "+user_name+" password "+password)
            
        else:
            #弹出error窗口
            msg_box = QtWidgets.QMessageBox(self)
            msg_box.setWindowTitle('Error!')
            msg_box.setInformativeText("不存在该用户或密码错误")
            msg_box.setIcon(QtWidgets.QMessageBox.Critical)
            msg_box.exec_()
            #self.logger.info("login failure: user "+user_name+" password "+password)