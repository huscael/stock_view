import threading
import socketserver
import json
import rsa
from Crypto.Cipher import AES
from customed_crypto import ServerCrypto
from db_sq3 import db
import tushare as ts
import datetime
from my_logger import MyLogger

HOST, PORT = "localhost", 12345
DB_NAME = "test.db"

#TODO 1.logging functionality 2.data localization
class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    '''
    client request handler
    '''
    def handle(self):
        '''
        handle request
        '''
        #log
        self.logger = MyLogger.getInstance("server.log")
        #读取服务器私钥
        with open("privateKey.pem", "r") as f:
            self.private_key = rsa.PrivateKey.load_pkcs1(f.read().encode())
        #服务器加密管理
        self.Crypto = ServerCrypto()
        self.Crypto.new_rsa(self.private_key)
        #服务器数据库管理
        self.db = db(DB_NAME)
        self.db.create_user_table()

        #消息读取循环
        while True:
            #接受客户端数据
            data_spec, data_recv = self.recv_data()
            #若客户端断开则退出
            if not data_recv:
                self.logger.info("client disconnected...")
                break
            #解密
            data_recv = self.Crypto.decrypt(data_spec, data_recv)
            self.logger.info("server received (crypto removed) from client "+str(threading.current_thread())+": "+json.dumps(data_recv))

            #客户端登陆处理
            if data_recv["type"] == "req_login":
                self.handle_login(data_recv)
            elif data_recv["type"] == "req_stock_kline":
                self.handle_kline(data_recv)
            elif data_recv["type"] == "req_stock_detail":
                self.handle_detail(data_recv)
            elif data_recv["type"] == "req_stock_list":
                self.handle_list(data_recv)
            elif data_recv["type"] == "live_check":
                self.send_data("2", dict({"type":"live_check"}))
            else:
                self.send_data("2", dict({"type":"error"}))

    def handle_login(self, data_recv):
        '''
        handle login event

        Args:
            data_recv: json data
        '''
        #构造返回数据
        data_response = dict()
        data_response["type"] = "ret_login"
        #读取数据库判断用户登陆是否成功
        if self.db.check_user(data_recv["user_name"], data_recv["password"]):
            data_response["auth"] = "correct"
        else:
            data_response["auth"] = "wrong"
        #aes加密
        self.client_aes_key, self.client_aes_iv = data_recv["aes_key"], data_recv["aes_iv"]
        self.Crypto.new_aes(AES.MODE_CBC, self.client_aes_key.encode(), self.client_aes_iv.encode())

        #发送数据
        self.send_data("1", data_response)

    def recv_data(self):
        '''
        receive data from client

        Returns:
            bytes without length and data_spec
        '''
        #读取包长度并转换为int
        data_len = self.request.recv(64).decode()
        #判断用户是否退出
        if not data_len :
            return None, None
        data_spec = self.request.recv(1).decode()
        data_len = int(data_len.strip())
        #按照length读取包
        data_recv = self.request.recv(data_len)

        self.logger.info("server received from client "+str(threading.current_thread())+":")
        self.logger.info(data_recv)
        return data_spec,data_recv

    def send_data(self, data_spec, data_response):
        '''
        send data to client

        Args:
            data_spec: encrypt method specification in string format
            data_response: json
        '''
        #加密
        data_response_encrypted = self.Crypto.encrypt(data_spec, data_response)
        
        #计算paylod长度
        data_len = str(len(data_response_encrypted))
        data_len += ' '*(64-len(data_len))

        #返回数据转换为bytes并添加length头
        data_response_bytes = data_len.encode()+data_spec.encode()+data_response_encrypted
        #print("server sent:")
        #print(data_len+json.dumps(data_response))
        self.logger.info("server sent data_len "+str(data_len))
        self.logger.info("server sent data length "+str(len(data_response_encrypted)))

        #发送
        self.request.sendall(data_response_bytes)

    def handle_kline(self, recv_data):
        '''
        handle k-line data request

        Args:
            recv_data: json
        '''
        #查询数据
        stock_code = recv_data["stock_code"]
        start_date_str = recv_data["start_date"]
        end_date_str = recv_data["end_date"]
        data = ts.get_hist_data(code=stock_code, start=start_date_str, end=end_date_str).sort_index()

        #构造返回数据
        data_response = dict()
        data_response["type"] = "ret_stock_kline"
        data_response["data"] = data.to_json(orient = "columns")

        #发送数据
        self.send_data("1", data_response)

    def handle_detail(self, recv_data):
        '''
        handle stock detail data request

        Args:
            recv_data: json
        '''
        #查询数据库
        detail = self.db.read_all("stockDetail")
        
        #构造返回数据
        data_response = dict()
        data_response["type"] = "ret_stock_detail"
        data_response["data"] = json.dumps(detail)

        #发送数据
        self.send_data("1", data_response)

    def handle_list(self, recv_data):
        '''
        handle stock list data request

        Args:
            recv_data: json
        '''
        #查询数据库
        stock_list = self.db.read_all("stockList")

        #构造返回数据
        data_response = dict()
        data_response["type"] = "ret_stock_list"
        data_response["data"] = json.dumps(stock_list)

        #发送数据
        self.send_data("1", data_response)

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

if __name__ == "__main__":
    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()
