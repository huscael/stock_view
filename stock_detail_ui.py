import time, datetime, os
import numpy as np
import pyqtgraph as pg
from client_model import ClientModel
import traceback

from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
from pyqtgraph.python2_3 import asUnicode
from pyqtgraph.Point import Point
from pyqtgraph import debug as debug
import weakref
from pyqtgraph import functions as fn
from pyqtgraph import getConfigOption

class DateAxis(pg.AxisItem):
    '''
    customized axis for displaying datetime
    '''
    def __init__(self, *args, **kargs):
        pg.AxisItem.__init__(self, *args, **kargs)
    def setTime(self, seconds):
        '''
        set datetime list

        Args:
            seconds: datetime in seconds format, counted from 1970/1/1 08:00:00
        '''
        self.seconds = seconds
    def tickStrings(self, values, scale, spacing):
        strs = []
        if not values:
            return pg.AxisItem.tickStrings(self, values, scale, spacing)
        rng = max(values)-min(values)
 
        if rng < 3600*24:
            string = '%H:%M:%S'
        elif rng >= 3600*24 and rng < 3600*24*30:
            string = '%d'
        elif rng >= 3600*24*30 and rng < 3600*24*30*24:
            string = '%b'
        elif rng >=3600*24*30*24:
            string = '%Y'
        
        #values中为index下标，将其转换为对应datetime
        for x in values:
            try:
                x = self.seconds[int(x)]
                strs.append(time.strftime(string, time.localtime(x)))
            except:
                strs.append(x)
        return strs

class RightAxis(pg.AxisItem):
    '''
    customized axis for displaying percentage data
    '''
    def __init__(self, *args, **kargs):
        pg.AxisItem.__init__(self, *args, **kargs)

    def setAverage(self, value):
        '''
        设置昨日收盘价

        Args:
            value: 昨日收盘价
        '''
        self.avg_v = value

    def tickStrings(self, values, scale, spacing):
        strs = []
        if not values:
            return pg.AxisItem.tickStrings(self, values, scale, spacing)
 
        #转换为百分比
        for x in values:
            try:
                x = (x-self.avg_v)*100/self.avg_v
                strs.append("{:.2f}%".format(x))
            except:
                strs.append(x)
        return strs
    
    def drawPicture(self, p, axisSpec, tickSpecs, textSpecs):
        profiler = debug.Profiler()

        p.setRenderHint(p.Antialiasing, False)
        p.setRenderHint(p.TextAntialiasing, True)
        
        ## draw long line along axis
        pen, p1, p2 = axisSpec
        p.setPen(pen)
        p.drawLine(p1, p2)
        p.translate(0.5,0)  ## resolves some damn pixel ambiguity
        
        ## draw ticks
        for pen, p1, p2 in tickSpecs:
            p.setPen(pen)
            p.drawLine(p1, p2)
        profiler('draw ticks')

        ## Draw all text
        if self.tickFont is not None:
            p.setFont(self.tickFont)
        p.setPen(self.pen())
        for rect, flags, text in textSpecs:
            if float(text[:-1]) > 0:
                p.setPen(pg.mkPen('r'))
            else:
                p.setPen(pg.mkPen('g'))
            p.drawText(rect, flags, text)
            #p.drawRect(rect)
        profiler('draw text')

class LeftAxis(pg.AxisItem):
    '''
    customized axis for displaying percentage data
    '''
    def __init__(self, *args, **kargs):
        pg.AxisItem.__init__(self, *args, **kargs)

    def setAverage(self, value):
        '''
        设置昨日收盘价

        Args:
            value: 昨日收盘价
        '''
        self.avg_v = value

    def drawPicture(self, p, axisSpec, tickSpecs, textSpecs):
        profiler = debug.Profiler()

        p.setRenderHint(p.Antialiasing, False)
        p.setRenderHint(p.TextAntialiasing, True)
        
        ## draw long line along axis
        pen, p1, p2 = axisSpec
        p.setPen(pen)
        p.drawLine(p1, p2)
        p.translate(0.5,0)  ## resolves some damn pixel ambiguity
        
        ## draw ticks
        for pen, p1, p2 in tickSpecs:
            p.setPen(pen)
            p.drawLine(p1, p2)
        profiler('draw ticks')

        ## Draw all text
        if self.tickFont is not None:
            p.setFont(self.tickFont)
        p.setPen(self.pen())
        for rect, flags, text in textSpecs:
            if float(text)-self.avg_v > 1e-6:
                p.setPen(pg.mkPen('r'))
            else:
                p.setPen(pg.mkPen('g'))
            p.drawText(rect, flags, text)
            #p.drawRect(rect)
        profiler('draw text')

class StockDetailWindow(pg.GraphicsWindow):
    def __init__(self, client_model):
        super(StockDetailWindow, self).__init__(title = "股票详情")

        #cs通信
        self.client_model = client_model
    
        #数据本地化，查看是否需要请求服务器
        if os.path.exists("stock_detail_local.txt"):
            file_mdate = datetime.datetime.fromtimestamp(os.path.getmtime("stock_detail_local.txt"))
            today = datetime.datetime.today()
            if (file_mdate.year, file_mdate.month, file_mdate.day) == (today.year, today.month, today.day):
                with open("stock_detail_local.txt", "r") as f:
                    lines = f.readlines()
                    self.data = list(map(lambda x:x.split('\t')[0:4], lines))
            else:
                self.data = self.client_model.query_stock_detail()
                #持久化到本地
                with open("stock_detail_local.txt", "w") as f:
                    f_lines = map(lambda x: '\t'.join(list(map(lambda y: str(y), x)))+'\t\n', self.data)
                    f.writelines(f_lines)
        else:
            self.data = self.client_model.query_stock_detail()
            #持久化到本地
            with open("stock_detail_local.txt", "w") as f:
                f_lines = map(lambda x: '\t'.join(list(map(lambda y: str(y), x)))+'\t\n', self.data)
                f.writelines(f_lines)

        self.draw()

    def date2sec(self, date):
        '''
        计算与1970/01/01 08:00:00的差值，以秒为单位

        Args:
            date: datetime date, format specified by server

        Returns:
            与1970/01/01 08:00:00的差值，以秒为单位
        '''
        time_1 = datetime.datetime(int(date[0:4]), int(date[5:7]), int(date[8:10]), int(date[10:12]), int(date[13:15]), int(date[16:18]))
        time_2 = datetime.datetime(1970, 1, 1, 8, 0, 0)
        return (time_1-time_2).seconds

    def handle_data(self):
        '''
        处理数据
        '''
        #横坐标x format:2019-12-2415:00:03
        x = list(map(lambda x_:x_[0], self.data))
        self.seconds = list(map(self.date2sec, x))
        #纵坐标y1 当前价
        self.y1 = list(map(lambda x_:float(x_[1]), self.data))
        self.y1.reverse() #数据文件倒序
        #纵坐标y2 均价
        self.y2 = list(map(lambda x_:float(x_[2])/float(x_[3])/100, self.data))
        self.y2.reverse()
        #纵坐标y3 成交量
        self.y3 = list(map(lambda x_:int(x_[3]), self.data))
        self.y3.reverse()
        for i in range(len(self.y3)):
            if i<len(self.y3)-1:
                self.y3[i] = self.y3[i+1]-self.y3[i]
            else:
                self.y3[i] = 0
        '''
        #纵坐标y2 点均价
        self.y2 = list(map(lambda x_:float(x_[2]), self.data))
        self.y2.reverse()
        for i in range(len(self.y2)):
            if self.y3[i] != 0:
                if i < len(self.y2):
                    self.y2[i] = (self.y2[i+1]-self.y2[i])/self.y3[i]/100
                else:
                    self.y2[i] = self.y2[i-1]
            else:
                if i > 0:
                    self.y2[i] = self.y2[i-1]
                else:
                    self.y2[i] = 0
        '''

    def draw(self):
        '''
        产生股票行情界面
        '''
        
        #右上角label用于显示信息
        self.label = pg.LabelItem(justify='right')
        self.addItem(self.label)

        # Enable antialiasing for prettier plots
        pg.setConfigOptions(antialias=True)

        #处理数据
        self.handle_data()
        
        #costumize axis
        data_axis= DateAxis(orientation='bottom') #bottom axis
        self.seconds.reverse() #数据文件倒序
        data_axis.setTime(self.seconds)
        data_axis_2= DateAxis(orientation='bottom') #bottom axis
        data_axis_2.setTime(self.seconds)

        right_axis = RightAxis(orientation = "right") #right axis
        right_axis.setAverage(np.median(self.y1))

        #生成函数图像p1,p2
        self.p1 =self.addPlot(row=1, col=0, axisItems={'bottom': data_axis, 'right': right_axis})
        self.p1.getAxis("left").setWidth(60)
        self.p1.getAxis("right").setWidth(60)
        self.p1.showAxis('right')
        self.p1.hideAxis("bottom")
        self.p2 =self.addPlot(row=2, col=0, axisItems={'bottom': data_axis_2})
        self.p2.getAxis("left").setWidth(60)
        self.p2.getAxis("right").setWidth(60)
        self.p2.showAxis('right')
        self.p1.plot(x=list(range(len(self.y1))), y=self.y1, fillLevel= min(self.y2)-0.1, brush = (50, 50, 200, 50))
        self.p1.plot(x=list(range(len(self.y2))), y=self.y2, pen=(255, 255, 0))
        bar_graph = pg.BarGraphItem(x=range(len(self.y3)), height=self.y3, width=0.3, brush='y')
        self.p2.addItem(bar_graph)
        self.p1.showGrid(x=True, y=True)
        self.p2.showGrid(x=True, y=True)
        self.p1.setAutoVisible(y=True)
        self.p2.setAutoVisible(y=True)

        #图像初始化设置
        self.x_range = (0, len(self.y2)/10)
        self.p1.setXRange(self.x_range[0], self.x_range[1])
        self.p2.setXRange(self.x_range[0], self.x_range[1])
        self.p1.setLimits(xMin = 0, xMax = len(self.y1)-1, yMin = min(*self.y1, *self.y2)-0.05, yMax = max(*self.y1, *self.y2))
        self.p2.setLimits(xMin = 0, xMax = len(self.y1)-1, yMin = min(self.y3)-10, yMax = max(self.y3))
        self.p1.setYRange(min(*self.y1, *self.y2)-0.05, max(*self.y1, *self.y2))

        self.cross_hair()

        #self.setRegion()

        #self.p2.sigRangeChanged.connect(self.update_p1)
        self.p2.setXLink(self.p1)

        #绑定鼠标移动事件
        self.proxy_p1 = pg.SignalProxy(self.p1.scene().sigMouseMoved, rateLimit=80, slot=self.mouseMoved_p1)
        self.proxy_p2 = pg.SignalProxy(self.p2.scene().sigMouseMoved, rateLimit=80, slot=self.mouseMoved_p2)

    def setRegion(self):
        self.region = pg.LinearRegionItem()
        self.region.setZValue(10)
        self.p2.addItem(self.region, ignoreBounds=True)

        self.region.sigRegionChanged.connect(self.update)
        self.p1.sigRangeChanged.connect(self.update_region)
        self.region.setRegion([0, 100])

    def update(self):
        '''
        根据region组件显示范围更新p1显示范围
        '''
        self.region.setZValue(10)
        minX, maxX = self.region.getRegion()
        self.p1.setXRange(minX, maxX, padding=0)    
    
    def update_region(self, window, viewRange):
        '''
        根据p1显示范围更新region组件显示范围
        '''
        rgn = viewRange[0]
        self.region.setRegion(rgn)
    
    def cross_hair(self):
        '''
        随鼠标移动产生十字光标
        '''
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.hLine = pg.InfiniteLine(angle=0, movable=False)
        self.vLine_p2 = pg.InfiniteLine(angle=90, movable=False)
        self.hLine_p2 = pg.InfiniteLine(angle=0, movable=False)
        self.p2.addItem(self.vLine, ignoreBounds=True)
        self.p2.addItem(self.hLine, ignoreBounds=True)
        self.p1.addItem(self.vLine_p2, ignoreBounds=True)
        self.p1.addItem(self.hLine_p2, ignoreBounds=True)

    def mouseMoved_p1(self, evt):
        '''
        鼠标移动事件
        '''
        pos = evt[0]  ## using signal proxy turns original arguments into a tuple
        if self.p1.sceneBoundingRect().contains(pos):
            mousePoint = self.p1.vb.mapSceneToView(pos)
            index = int(mousePoint.x())
            if index > 0 and index < len(self.y1):
                self.label.setText("<span style='font-size: 12pt'>时间=%s</span>, <span style='color: white'>当前价=%0.3f</span>, <span style='color: yellow'>成交量=%d</span>, <span style='color: yellow'>均价=%0.3f</span>" % (time.strftime('%H:%M:%S', time.localtime(self.seconds[index])), self.y1[index], self.y3[index], self.y2[index]))
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())
            self.vLine_p2.setPos(mousePoint.x())
            self.hLine_p2.setPos(mousePoint.y())

    def mouseMoved_p2(self, evt):
        '''
        鼠标移动事件
        '''
        pos = evt[0]  ## using signal proxy turns original arguments into a tuple
        if self.p2.sceneBoundingRect().contains(pos):
            mousePoint = self.p2.vb.mapSceneToView(pos)
            index = int(mousePoint.x())
            if index > 0 and index < len(self.y1):
                self.label.setText("<span style='font-size: 12pt'>时间=%s</span>, <span style='color: white'>当前价=%0.3f</span>, <span style='color: yellow'>成交量=%d</span>, <span style='color: yellow'>均价=%0.3f</span>" % (time.strftime('%H:%M:%S', time.localtime(self.seconds[index])), self.y1[index], self.y3[index], self.y2[index]))
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())
            self.vLine_p2.setPos(mousePoint.x())
            self.hLine_p2.setPos(mousePoint.y())

class StockDetailWindowImproved(QtWidgets.QWidget):
    def __init__(self):
        super(StockDetailWindowImproved, self).__init__()

        #cs通信
        self.client_model = ClientModel.getInstance()
    
        #数据本地化，查看是否需要请求服务器
        if os.path.exists("stock_detail_local.txt"):
            file_mdate = datetime.datetime.fromtimestamp(os.path.getmtime("stock_detail_local.txt"))
            today = datetime.datetime.today()
            if (file_mdate.year, file_mdate.month, file_mdate.day) == (today.year, today.month, today.day):
                with open("stock_detail_local.txt", "r") as f:
                    lines = f.readlines()
                    self.data = list(map(lambda x:x.split('\t')[0:4], lines))
            else:
                self.data = self.client_model.query_stock_detail()
                #持久化到本地
                with open("stock_detail_local.txt", "w") as f:
                    f_lines = map(lambda x: '\t'.join(list(map(lambda y: str(y), x)))+'\t\n', self.data)
                    f.writelines(f_lines)
        else:
            self.data = self.client_model.query_stock_detail()
            #持久化到本地
            with open("stock_detail_local.txt", "w") as f:
                f_lines = map(lambda x: '\t'.join(list(map(lambda y: str(y), x)))+'\t\n', self.data)
                f.writelines(f_lines)

        self.draw()

    def date2sec(self, date):
        '''
        计算与1970/01/01 08:00:00的差值，以秒为单位

        Args:
            date: datetime date, format specified by server

        Returns:
            与1970/01/01 08:00:00的差值，以秒为单位
        '''
        time_1 = datetime.datetime(int(date[0:4]), int(date[5:7]), int(date[8:10]), int(date[10:12]), int(date[13:15]), int(date[16:18]))
        time_2 = datetime.datetime(1970, 1, 1, 8, 0, 0)
        return (time_1-time_2).seconds

    def handle_data(self):
        '''
        处理数据
        '''
        #横坐标x format:2019-12-2415:00:03
        x = list(map(lambda x_:x_[0], self.data))
        self.seconds = list(map(self.date2sec, x))
        #纵坐标y1 当前价
        self.y1 = list(map(lambda x_:float(x_[1]), self.data))
        self.y1.reverse() #数据文件倒序
        #纵坐标y2 均价
        self.y2 = list(map(lambda x_:float(x_[2])/float(x_[3])/100, self.data))
        self.y2.reverse()
        #纵坐标y3 成交量
        self.y3 = list(map(lambda x_:int(x_[3]), self.data))
        self.y3.reverse()
        for i in range(len(self.y3)):
            if i<len(self.y3)-1:
                self.y3[i] = self.y3[i+1]-self.y3[i]
            else:
                self.y3[i] = 0
        '''
        #纵坐标y2 点均价
        self.y2 = list(map(lambda x_:float(x_[2]), self.data))
        self.y2.reverse()
        for i in range(len(self.y2)):
            if self.y3[i] != 0:
                if i < len(self.y2):
                    self.y2[i] = (self.y2[i+1]-self.y2[i])/self.y3[i]/100
                else:
                    self.y2[i] = self.y2[i-1]
            else:
                if i > 0:
                    self.y2[i] = self.y2[i-1]
                else:
                    self.y2[i] = 0
        '''

    def draw(self):
        '''
        产生股票行情界面
        '''
        self.layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.layout) 
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        #右上角label用于显示信息
        self.label = pg.LabelItem(justify='right')
        self.p_label = pg.GraphicsLayoutWidget(self)
        self.p_label.addItem(self.label)
        self.layout.addWidget(self.p_label)

        # Enable antialiasing for prettier plots
        pg.setConfigOptions(antialias=True)

        #处理数据
        self.handle_data()
        
        #costumize axis
        data_axis= DateAxis(orientation='bottom') #bottom axis
        self.seconds.reverse() #数据文件倒序
        data_axis.setTime(self.seconds)
        data_axis_2= DateAxis(orientation='bottom') #bottom axis
        data_axis_2.setTime(self.seconds)

        right_axis = RightAxis(orientation = "right") #right axis
        right_axis.setAverage(np.median(self.y1))
        left_axis = LeftAxis(orientation = "left") #right axis
        left_axis.setAverage(np.median(self.y1))

        #生成函数图像p1,p2
        self.p1 =pg.PlotWidget(axisItems={'bottom': data_axis, 'right': right_axis, 'left': left_axis})
        self.p1.getAxis("left").setWidth(60)
        self.p1.getAxis("right").setWidth(60)
        self.p1.showAxis('right')
        self.p1.showAxis('left')
        self.p1.hideAxis("bottom")
        #self.p1.addItem(self.label)
        self.layout.addWidget(self.p1)
        self.p2 =pg.PlotWidget(axisItems={'bottom': data_axis_2})
        self.p2.getAxis("left").setWidth(60)
        self.p2.getAxis("left").setPen(pg.mkPen('y'))
        self.p2.getAxis("right").setWidth(60)
        self.p2.getAxis("right").setPen(pg.mkPen('y'))
        self.p2.getAxis("bottom").setPen(pg.mkPen('y'))
        self.p2.showAxis('right')
        self.layout.addWidget(self.p2)
        self.p1.plot(x=list(range(len(self.y1))), y=self.y1, fillLevel= min(self.y2)-0.1, brush = (50, 50, 200, 50))
        self.p1.plot(x=list(range(len(self.y2))), y=self.y2, pen=(255, 255, 0))
        bar_graph = pg.BarGraphItem(x=range(len(self.y3)), height=self.y3, width=0.3, brush='y')
        self.p2.addItem(bar_graph)
        self.p1.showGrid(x=True, y=True)
        self.p2.showGrid(x=True, y=True)
        self.p1.setAutoVisible(y=True)
        self.p2.setAutoVisible(y=True)

        #图像初始化设置
        self.x_range = (0, len(self.y2)/10)
        self.p1.setXRange(self.x_range[0], self.x_range[1])
        self.p2.setXRange(self.x_range[0], self.x_range[1])
        self.p1.setLimits(xMin = 0, xMax = len(self.y1)-1, yMin = min(*self.y1, *self.y2)-0.05, yMax = max(*self.y1, *self.y2))
        self.p2.setLimits(xMin = 0, xMax = len(self.y1)-1, yMin = min(self.y3)-10, yMax = max(self.y3))
        self.p1.setYRange(min(*self.y1, *self.y2)-0.05, max(*self.y1, *self.y2))

        self.cross_hair()

        self.p2.setXLink(self.p1)

        #绑定鼠标移动事件
        self.proxy_p1 = pg.SignalProxy(self.p1.scene().sigMouseMoved, rateLimit=80, slot=self.mouseMoved_p1)
        self.proxy_p2 = pg.SignalProxy(self.p2.scene().sigMouseMoved, rateLimit=80, slot=self.mouseMoved_p2)

    def cross_hair(self):
        '''
        随鼠标移动产生十字光标
        '''
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.hLine = pg.InfiniteLine(angle=0, movable=False)
        self.vLine_p2 = pg.InfiniteLine(angle=90, movable=False)
        self.hLine_p2 = pg.InfiniteLine(angle=0, movable=False)
        self.p2.addItem(self.vLine, ignoreBounds=True)
        self.p2.addItem(self.hLine, ignoreBounds=True)
        self.p1.addItem(self.vLine_p2, ignoreBounds=True)
        self.p1.addItem(self.hLine_p2, ignoreBounds=True)

    def mouseMoved_p1(self, evt):
        '''
        鼠标移动事件
        '''
        pos = evt[0]  ## using signal proxy turns original arguments into a tuple
        if self.p1.sceneBoundingRect().contains(pos):
            mousePoint = self.p1.getPlotItem().vb.mapSceneToView(pos)
            index = int(mousePoint.x())
            if index > 0 and index < len(self.y1):
                self.label.setText("<span style='font-size: 12pt'>时间=%s</span>, <span style='color: white'>当前价=%0.3f</span>, <span style='color: yellow'>成交量=%d</span>, <span style='color: yellow'>均价=%0.3f</span>" % (time.strftime('%H:%M:%S', time.localtime(self.seconds[index])), self.y1[index], self.y3[index], self.y2[index]))
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())
            self.vLine_p2.setPos(mousePoint.x())
            self.hLine_p2.setPos(mousePoint.y())

    def mouseMoved_p2(self, evt):
        '''
        鼠标移动事件
        '''
        pos = evt[0]  ## using signal proxy turns original arguments into a tuple
        if self.p2.sceneBoundingRect().contains(pos):
            mousePoint = self.p2.getPlotItem().vb.mapSceneToView(pos)
            index = int(mousePoint.x())
            if index > 0 and index < len(self.y1):
                self.label.setText("<span style='font-size: 12pt'>时间=%s</span>, <span style='color: white'>当前价=%0.3f</span>, <span style='color: yellow'>成交量=%d</span>, <span style='color: yellow'>均价=%0.3f</span>" % (time.strftime('%H:%M:%S', time.localtime(self.seconds[index])), self.y1[index], self.y3[index], self.y2[index]))
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())
            self.vLine_p2.setPos(mousePoint.x())
            self.hLine_p2.setPos(mousePoint.y())

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    client_model = ClientModel()
    client_model.login("admin", "123456")
    win = StockDetailWindowImproved()
    win.resize(1000,600)
    win.show()
    app.exec_()