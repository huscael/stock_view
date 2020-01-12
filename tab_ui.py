from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import QDialog, QTabWidget
from kline_ui import KLineWidget
from stock_detail_ui import StockDetailWindow, StockDetailWindowImproved
from client_model import ClientModel
import sip

class KLine(QDialog):
    '''
    k-line graph in tabWidget
    '''
    def __init__(self, parent=None):
        '''
        initializing

        Args:
            parent: parent widget
        '''
        super(KLine, self).__init__(parent)

        self.client_model = ClientModel.getInstance()

        self.grid_layout = QtWidgets.QGridLayout(self)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.grid_layout)

        self.kline_now = None
    
    def load_kline(self, stock_info):
        '''
        load new k-line graph every time

        Args:
            stock_info: list, [stock_code(str), stock_name(str)]
        '''
        #if k-line graph not exist then create one, else remove old one first.
        if self.kline_now is None:
            self.kline_now = KLineWidget(stock_info)
            self.grid_layout.addWidget(self.kline_now)
        else:
            self.grid_layout.removeWidget(self.kline_now)
            sip.delete(self.kline_now)
            self.kline_now = KLineWidget(stock_info)
            self.grid_layout.addWidget(self.kline_now)

class StockDetail(QDialog):
    '''
    k-line graph in tabWidget
    '''
    def __init__(self, parent=None):
        '''
        initializing

        Args:
            parent: parent widget
        '''
        super(StockDetail, self).__init__(parent)

        self.client_model = ClientModel.getInstance()

        self.grid_layout = QtWidgets.QGridLayout(self)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)

        self.stock_detail_now = None

    def load_stock_detail(self):
        '''
        load new stock detail graph every time
        '''
        #if stock detail graph not exist then create one, else remove old one first.
        if self.stock_detail_now is None:
            self.stock_detail_now = StockDetailWindowImproved()
            self.grid_layout.addWidget(self.stock_detail_now)
        else:
            self.grid_layout.removeWidget(self.stock_detail_now)
            sip.delete(self.stock_detail_now)
            self.stock_detail_now = StockDetailWindowImproved()
            self.grid_layout.addWidget(self.stock_detail_now)

class TabView(QtWidgets.QWidget):
    '''
    tab view, including k-line graph and stock detail graph
    '''
    def __init__(self, parent=None):
        '''
        initializing

        Args:
            parent: parent widget
        '''
        super(TabView, self).__init__(parent)

        self.resize(400, 300)
        #建立tab界面垂直布局
        self.layout= QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        #建立tab界面
        self.tab_widget = QtWidgets.QTabWidget(self)
        self.layout.addWidget(self.tab_widget)
        self.kline_widget =KLine(self.tab_widget)
        self.stock_detail_widget =StockDetail(self.tab_widget)
        self.tab_widget.addTab(self.kline_widget, u"K线图")
        self.tab_widget.addTab(self.stock_detail_widget, u"股票行情")

        #返回按钮
        self.return_btn = QtWidgets.QPushButton(self)
        self.return_btn.clicked.connect(lambda : self.parentWidget().setCurrentIndex(1))
        self.return_btn.setText("返回")
        self.layout.addWidget(self.return_btn)
    
    def lazy_load(self, stock_info):
        '''
        load k-line graph and stock detail graph only when double clicked stock list

        Args:
            stock_info: stock info in stock list, format: [stock_code(str), stock_name(str)]
        '''
        self.kline_widget.load_kline(stock_info)
        self.stock_detail_widget.load_stock_detail()

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    t = TabView(ClientModel(), "600519 大唐控股")
    t.show()
    app.exec_()