from PyQt5 import QtWidgets, QtGui, QtCore
import pyqtgraph as pg
import datetime
import tushare as ts
from client_model import ClientModel
import pandas
import traceback
from my_logger import MyLogger
import math

class KLineWidget(QtWidgets.QMainWindow):
    '''
    k-line graph
    '''
    def __init__(self, stock_info):
        super().__init__()
        #cs通信
        self.client_model = ClientModel.getInstance()
        #log
        #self.logger = MyLogger().get_logger()
        #默认stock code: 600519
        self.stock_code = stock_info[0]

        self.setWindowTitle("A股股票历史走势K线图")
        self.main_widget = QtWidgets.QWidget() # 创建一个主部件
        self.main_layout = QtWidgets.QGridLayout() # 创建一个网格布局
        self.main_widget.setLayout(self.main_layout) # 设置主部件的布局为网格
        self.setCentralWidget(self.main_widget) # 设置窗口默认部件

        self.info_header = QtWidgets.QLineEdit() # 创建一个股票代码显示
        self.info_header.setReadOnly(True)
        self.info_header.setText('股票代码:'+stock_info[0]+'  股票名称:'+stock_info[1])
        self.option_sel = QtWidgets.QComboBox() # 创建一个下拉框部件
        self.option_sel.addItem("近60天")
        self.option_sel.addItem("近180天")
        self.option_sel.addItem("近360天")
        self.que_btn = QtWidgets.QPushButton("查询") # 创建一个按钮部件
        self.k_widget = QtWidgets.QWidget() # 实例化一个widget部件作为K线图部件
        self.k_layout = QtWidgets.QGridLayout() # 实例化一个网格布局层
        self.k_widget.setLayout(self.k_layout) # 设置K线图部件的布局层
        self.k_plt_window = pg.GraphicsWindow()
        self.label = pg.LabelItem()
        #self.label.setFixedWidth(300)
        self.k_plt_window.addItem(self.label)
        self.k_plt = pg.PlotItem() # 实例化一个绘图部件
        self.k_plt_window.addItem(self.k_plt, row = 1, col = 0)
        self.k_layout.addWidget(self.k_plt_window) # 添加绘图部件到K线图部件的网格布局层

        # 将上述部件添加到布局层中
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.info_header,0,0,1,1)
        self.main_layout.addWidget(self.option_sel,0,1,1,1)
        self.main_layout.addWidget(self.que_btn,0,2,1,1)
        self.main_layout.addWidget(self.k_widget,1,0,3,3)
        
        self.que_btn.clicked.connect(self.query_slot) # 绑定按钮点击信号

       
    def plot_k_line(self):
        """
        根据用户选择的参数绘制k线图
        """
        y_min = self.data['low'].min()
        y_max = self.data['high'].max()
        data_list = []
        self.data_volume = []
        self.data_price_change = []
        self.data_p_change = []
        self.data_ma5 = []
        self.data_ma10 = []
        self.data_ma20 = []

        d = 0
        for dates, row in self.data.iterrows():
            # 将时间转换为数字
            #date_time = datetime.datetime.strptime(dates, '%Y-%m-%d')
            # t = date2num(date_time)
            open, high, close, low , volume, price_change, p_change, ma5, ma10, ma20= row[:10]
            y_min = min(y_min, open, high, close, low, ma5, ma10, ma20)
            y_max = max(y_max, open, high, close, low, ma5, ma10, ma20)
            datas = (d, open, close, low, high)
            data_list.append(datas)
            self.data_volume.append(volume)
            self.data_price_change.append(price_change)
            self.data_p_change.append(p_change)
            self.data_ma5.append(ma5)
            self.data_ma10.append(ma10)
            self.data_ma20.append(ma20)
            print(datas)
            d += 1
        self.axis_dict = dict(enumerate(self.data.index))

        axis_1 = [(i, list(self.data.index)[i]) for i in range(0, len(self.data.index), 2)]  # 获取日期值
        axis_2 = [(i, list(self.data.index)[i]) for i in range(0, len(self.data.index), 12)]
        axis_3 = [(i, list(self.data.index)[i]) for i in range(0, len(self.data.index), 30)]
        self.k_plt.getAxis("bottom").setTicks([axis_3, axis_2, axis_1, self.axis_dict.items()])

        self.k_plt.clear() # 清空绘图部件中的项
        item = CandlestickItem(data_list)  # 生成蜡烛图数据
        self.k_plt.addItem(item, )  # 在绘图部件中添加蜡烛图项目
        self.k_plt.plot(x = list(range(len(self.data_ma5))), y= self.data_ma5, pen = (172, 88, 250)) #AC58FA
        self.k_plt.plot(x = list(range(len(self.data_ma10))), y= self.data_ma10, pen = (1, 223, 1)) #01DF01
        self.k_plt.plot(x = list(range(len(self.data_ma20))), y= self.data_ma20, pen = (245, 218, 129)) #F5DA81
        self.k_plt.showGrid(x=True, y=True)  # 设置绘图部件显示网格线
        self.k_plt.setYRange(y_min-1,y_max+1)
        self.k_plt.setXRange(-2, len(self.data_ma5)+1)
        self.k_plt.setLimits(xMin = -2, xMax = len(self.data_ma5)+1, yMin = y_min-1, yMax = y_max+1)
        self.k_plt.setLabel(axis='left', text='指数')  # 设置Y轴标签
        self.k_plt.setLabel(axis='bottom', text='日期')  # 设置X轴标签

        self.vLine = pg.InfiniteLine(angle=90, movable=False, )  # 创建一个垂直线条
        self.hLine = pg.InfiniteLine(angle=0, movable=False, )  # 创建一个水平线条
        self.k_plt.addItem(self.vLine, ignoreBounds=True)  # 在图形部件中添加垂直线条
        self.k_plt.addItem(self.hLine, ignoreBounds=True)  # 在图形部件中添加水平线条
 
    def query_slot(self):
        """
        查询信号槽
        """
        try:
            self.que_btn.setEnabled(False)
            self.que_btn.setText("查询中…")
            date_sel = self.option_sel.currentText()[1:-1]
            start_date = datetime.datetime.today()-datetime.timedelta(days=int(date_sel)+1)
            start_date_str = datetime.datetime.strftime(start_date,"%Y-%m-%d")
            end_date = datetime.datetime.today()-datetime.timedelta(days=1)
            end_date_str = datetime.datetime.strftime(end_date,"%Y-%m-%d")
            #self.logger.info("stock code:"+self.code+",start date:"+start_date_str+",end data:"+end_date_str)
            #向服务器请求数据
            self.data = self.client_model.query_stock_kline(stock_code=self.stock_code, start_date=start_date_str, end_date=end_date_str)
            self.data.index = self.data.index.map(lambda x:x.date().strftime("%Y-%m-%d"))
            self.plot_k_line()
            self.que_btn.setEnabled(True)
            self.que_btn.setText("查询")

            self.move_slot = pg.SignalProxy(self.k_plt.scene().sigMouseMoved, rateLimit=60, slot=self.print_slot)
        except Exception as e:
            #self.logger.error(e)
            traceback.print_exc()
        
    def print_slot(self, event=None):
        """
        响应鼠标移动绘制十字光标
        """
        if event is None:
            print("事件为空")
        else:
            pos = event[0]  # 获取事件的鼠标位置
            try:
                # 如果鼠标位置在绘图部件中
                if self.k_plt.sceneBoundingRect().contains(pos):
                    mousePoint = self.k_plt.vb.mapSceneToView(pos)  # 转换鼠标坐标
                    index = int(mousePoint.x())  # 鼠标所处的X轴坐标
                    pos_y = int(mousePoint.y())  # 鼠标所处的Y轴坐标
                    if -1 < index < len(self.data.index):
                        # 在label中写入HTML
                        self.label.setText(
                            '''<span style='color:white'><strong>日期：{0}</strong></span>, 
                            <span style='color:white'>开盘：{1:.2f}</span>, 
                            <span style='color:white'>收盘：{2:.2f}</span>, 
                            <span style='color:red'>最高价：{3:.2f}</span>, 
                            <span style='color:green'>最低价：{4:.2f}</span>, 
                            <span style='color:#FF8000'>成交额：{5:.2f}</span>, 
                            <span style='color:#01DFD7'>价格变动：{6:.2f}</span>, 
                            <span style='color:#01DFD7'>振幅：{7:.3f}%</span>, 
                            <span style='color:#AC58FA'>ma5：{8:.2f}</span>, 
                            <span style='color:#01DF01'>ma10：{9:.2f}</span>, 
                            <span style='color:#F5DA81'>ma20：{10:.2f}</span>
                            '''.format(
                                self.axis_dict[index], self.data['open'][index], self.data['close'][index],
                                self.data['high'][index], self.data['low'][index],
                                self.data_volume[index], self.data_price_change[index], self.data_p_change[index],
                                self.data_ma5[index], self.data_ma10[index], self.data_ma20[index]))
                        #self.label.setPos(mousePoint.x(), mousePoint.y())  # 设置label的位置
                    # 设置垂直线条和水平线条的位置组成十字光标
                    self.vLine.setPos(mousePoint.x())
                    self.hLine.setPos(mousePoint.y())
            except Exception as e:
                #self.logger.error(e)
                traceback.print_exc()

class CandlestickItem(pg.GraphicsObject):
    """
    K线图绘制类
    """
    def __init__(self, data):
        pg.GraphicsObject.__init__(self)
        self.data = data  # data字段: 时间, 开盘价, 收盘价, 最低价, 最高价
        self.generatePicture()

    def generatePicture(self):
        self.picture = QtGui.QPicture() # 实例化一个绘图设备
        p = QtGui.QPainter(self.picture) # 在picture上实例化QPainter用于绘图
        p.setPen(pg.mkPen('w')) # 设置画笔颜色
        w = (self.data[1][0] - self.data[0][0]) / 3.
        for (t, open, close, min, max) in self.data:
            print(t, open, close, min, max)
            if min != max:
                p.drawLine(QtCore.QPointF(t, min), QtCore.QPointF(t, max)) # 绘制线条
            if open > close: # 开盘价大于收盘价
                p.setBrush(pg.mkBrush('g')) # 设置画刷颜色为绿
            else:
                p.setBrush(pg.mkBrush('r')) # 设置画刷颜色为红
            p.drawRect(QtCore.QRectF(t - w, open, w * 2, close - open)) # 绘制箱子
        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())

if __name__ == '__main__' :
    app = QtWidgets.QApplication([])
    client_model = ClientModel()
    client_model.login("admin", "123456")
    win = KLineWidget(["000001", "平安银行"])
    win.show()
    app.exec_()

