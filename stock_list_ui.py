import time, os, datetime
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtGui import QPen, QBrush, QPalette, QColor
from PyQt5.QtCore import Qt, QVariant, QThread, pyqtSignal
from tab_ui import TabView
from client_model import ClientModel
from my_logger import MyLogger
import sip

class StockListView(QtWidgets.QWidget):
    def __init__(self, parent = None):
        super(StockListView, self).__init__(parent)
        #cs通信
        self.client_model = ClientModel.getInstance()
        #log
        #self.logger = MyLogger().get_logger()
        #建立股票列表界面垂直布局
        self.setGeometry(QtCore.QRect(80, 40, 631, 471))
        self.layout= QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        #建立股票列表界面
        self.list_view = StockListWidget(self)
        #设置双击事件
        self.list_view.doubleClicked.connect(self.double_clicked)
        #将list_view加入垂直布局
        self.layout.addWidget(self.list_view)
        #返回按钮
        self.list_view_Btn = QtWidgets.QPushButton(self)
        self.list_view_Btn.clicked.connect(self.clicked)
        self.list_view_Btn.setText("退出账号")
        self.layout.addWidget(self.list_view_Btn)
        #将数据加载线程与列表界面链接

    
    def double_clicked(self, index):
        '''
        jump to tab view after double clicked

        Args:
            index: QModelIndex type, comprises index information
        '''
        self.parentWidget().setCurrentIndex(2)
        self.parentWidget().parentWidget().resize(1440, 900)
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        size = self.parentWidget().parentWidget().geometry()
        self.parentWidget().parentWidget().move((screen.width() - size.width()) / 2,
                  (screen.height() - size.height()) / 2)
        stock_code = self.list_view.list_model.item(index.row(), 1).text()
        stock_name = self.list_view.list_model.item(index.row(), 2).text()
        self.tabWidget.lazy_load([stock_code, stock_name])
    
    def clicked(self):
        '''
        return to login view
        '''
        self.parentWidget().setCurrentIndex(0)
        self.parentWidget().parentWidget().resize(350, 250)
        #centerize view
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        size = self.parentWidget().parentWidget().geometry()
        self.parentWidget().parentWidget().move((screen.width() - size.width()) / 2,
                  (screen.height() - size.height()) / 2)
    
    def set_tab(self, tabWidget):
        '''
        link tab view with stock list view to enable lazy load
        '''
        self.tabWidget = tabWidget

class StockListWidget(QtWidgets.QTreeView):
    '''
    draw stock list
    '''
    def __init__(self, parent):
        QtWidgets.QTreeView.__init__(self, parent = parent)
        #cs通信
        self.client_model = ClientModel.getInstance()
        #log
        #self.logger = MyLogger().get_logger()
        #建立股票列表界面
        self.list_model = QtGui.QStandardItemModel(0, 2, parent)
        self.setModel(self.list_model)
        #自动排序
        #self.setSortingEnabled(True)
        #载入列表内容
        #self.loadData()
        #设置delegate
        self.setItemDelegate(ListDelegate())
        #设置背景颜色为黑色
        self.setStyleSheet("QHeaderView{background:#303030;color:white}QTreeView{background:black}")

    def startLoader(self):
        '''
        load data
        '''
        #set header
        headers = ["序号", "股票代码", "股票名称", "昨日收盘价", "昨日结算价", "昨日持仓量", "涨停价", "跌停价",
        "总股本", "流通盘", "合约数量乘数", "最小变动价位", "上市日"]
        self.list_model.setHorizontalHeaderLabels(headers)
        length = len(headers)

        #数据本地化，查看是否需要请求服务器
        if os.path.exists("stock_list_local.txt"):
            file_mdate = datetime.datetime.fromtimestamp(os.path.getmtime("stock_list_local.txt"))
            today = datetime.datetime.today()
            #若数据未过期则取本地数据加载
            if (file_mdate.year, file_mdate.month, file_mdate.day) == (today.year, today.month, today.day):
                with open("stock_list_local.txt", "r") as f:
                    lines = f.readlines()
                    lines = list(map(lambda x:x.split('\t')[0:length], lines))
                #self.logger.info("stock list load from local file:")
            else:
                lines = self.client_model.query_stock_list()
                #持久化到本地
                with open("stock_list_local.txt", "w") as f:
                    f_lines = map(lambda x: '\t'.join(list(map(lambda y: str(y), x)))+'\t\n', lines)
                    f.writelines(f_lines)
                #self.logger.info("stock list load from server:")
        else:
            lines = self.client_model.query_stock_list()
            #持久化到本地
            with open("stock_list_local.txt", "w") as f:
                f_lines = map(lambda x: '\t'.join(list(map(lambda y: str(y), x)))+'\t\n', lines)
                f.writelines(f_lines)
            #self.logger.info("stock list load from server:")

        #to avoid data overflow
        lines = list(map(lambda x_: list(map(lambda y_: str(y_), x_)), lines))

        #preload data rows
        #self.list_model.insertRows(0, len(lines))

        #start thread to load data, to avoid dead interface
        self.loader = Loader(lines)
        self.loader.load.connect(self.loadData)  # 链接信号
        self.loader.finish.connect(self.repaint)
        self.loader.start()

    def loadData(self, data):
        '''
        load gird data to model

        Args:
            data: tuple type, format:(row, col, data)
        '''
        #start_time = time.time()
        self.list_model.appendRow(data)
        #self.list_model.setItem(data[0], data[1], QtGui.QStandardItem(str(data[2])))
        #self.list_model.setData(self.list_model.index(data[0], data[1]), QVariant(str(data[2])))
        #end_time = time.time()
        #print("load to view:", end_time-start_time)
    
class ListDelegate(QtWidgets.QItemDelegate):
    '''
    control data appearance
    '''
    def __init__(self):
        super(ListDelegate, self).__init__()

    def paint(self, painter, option, index):
        painter.save()

        # set background color
        painter.setPen(QPen(Qt.NoPen))
        painter.setBrush(QBrush(Qt.black))
        painter.drawRect(option.rect)

        # set text color
        if index.column() == 1:
            painter.setPen(QPen(Qt.blue))
        elif index.column() == 2:
            painter.setPen(QPen(Qt.yellow))
        elif index.column() == 6:
            painter.setPen(QPen(Qt.red))
        elif index.column() == 7:
            painter.setPen(QPen(Qt.green))
        else:
            painter.setPen(QPen(Qt.white))
        value = index.data(Qt.DisplayRole)
        painter.drawText(option.rect, Qt.AlignLeft, str(value))

        painter.restore()

class Loader(QThread):
    '''
    Thread used to concurrently load stock list data
    '''
    load = pyqtSignal(tuple) #load signal
    finish = pyqtSignal()

    def __init__(self, lines):
        '''
        initializing

        Args:
            lines: list data ready to load, format: [[col1, col2, ..., coln], ...]
        '''
        super(Loader, self).__init__()
        self.lines = lines
        self.start_time = time.time()

    def run(self):
        '''
        run after thread started

        emit load signal at every grid to call function to actually update data
        '''
        #logger = MyLogger().get_logger()
        #logger.info("stock list data loading thread running...")

        for row, line in enumerate(self.lines):
            items = []
            for col, grid in enumerate(line):
                items.append(QtGui.QStandardItem(str(grid)))
            self.load.emit(tuple(items))
            #self.load.emit((row, col, grid))

        print("thread finish time", time.time()-self.start_time)
        self.finish.emit()
        
if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    client_model = ClientModel()
    client_model.login("admin", "123456")
    widget = StockListView(client_model)
    widget.show()
    app.exec_()