# stock_view
school project

C/S架构，具有登陆功能、断线重连（心跳机制）、股票列表、k线图展示（tushare获取）、股票行情展示（demo）等功能

GUI界面使用pyqt5，股票列表使用Qthread多线程加载，服务端采用socketserver多线程

使用方法：
1. 运行客户端
```python
python main.py
```
2. 运行服务端
```python
python server_model.py
```

第三方库需求：PyQt5、pyqtgraph、tushare、pandas、numpy、sip、sqlite3、gzip、Crypto、rsa
