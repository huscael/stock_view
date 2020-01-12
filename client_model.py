import socket
import json
import rsa
import random
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from customed_crypto import ClientCrypto
import pandas
import threading
import time
import traceback
from my_logger import MyLogger
from PyQt5.QtCore import QThread, pyqtSignal

HOST, PORT = "localhost", 12345

class ClientModel(object):
    '''
    c/s communication protocal:
        data format: length+specify+{'key1':stringvalue, 'key2':stringvalue}
        data packet length parameter is fixed at 64 bytes with no ctypto mask, specify occupy 1 byte (0/1)
        important keys for identification: type ("", "req_login", "req_stock_list", "req_stock_detail", "req_stock_kline")
        request login: {"type": "req_login", "user_name": stringvalue, "password": stringvalue}
            return: {"type": "ret_login", "auth": "correct"/"wrong"}
        request stock list: {"type": "req_stock_list"}
        request stock detail: {"type": "req_stock_detail", "stock_code": stringvalue}
        request stock kline: {"type": "req_stock_kline", "stock_code": stringvalue}
            return: {"type": "ret_stock_kline", "data": data}
    '''
    __instance = None

    @staticmethod
    def getInstance(ip = HOST, port = PORT):
        """
        Static access method, get ClientModel instance

        Args:
            ip: server ip
            port: server port
        """
        if ClientModel.__instance == None:
            ClientModel(ip, port)
        return ClientModel.__instance
    
    def __init__(self, ip = HOST, port = PORT): 
        """
        initializing

        Args:
            ip: server ip
            port: server port
        """
        if ClientModel.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            ClientModel.__instance = self
        #log
        self.logger = MyLogger.getInstance("client.log")
        #server ip and port
        self.ip, self.port = ip, port
        #TCP socket建立
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.ip, self.port))
        #建立锁
        self.mutex = threading.Lock()
        #读取服务器公钥
        with open("publicKey.pem", "r") as f:
            self.server_public_key = rsa.PublicKey.load_pkcs1(f.read().encode())

        self.Crypto = ClientCrypto()
        self.Crypto.new_rsa(self.server_public_key)
        self.logger.info("client model initializd successfully...")

    '''
    def server_live_check(self):
        """
        check if server is alive, try reconnect dead server
        """
        while True:
            try:
                data = dict()
                data["type"] = "live_check"
                self.mutex.acquire()
                self.send_data(data)
                self.recv_data()
                self.logger.info("socket connection condition check: good")
            except:
                self.logger.info("socket error, try reconnect...")
                try:
                    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.sock.connect((self.ip, self.port))

                    data_re = dict()
                    data_re["type"] = "req_login"
                    data_re["user_name"] = self.user_name
                    data_re["password"] = self.password
                    #建立aes加密对象
                    data_re["aes_key"], data_re["aes_iv"] = self.Crypto.new_aes(AES.MODE_CBC)

                    #发送数据
                    self.send_data(data_re)
                    #接受服务端数据
                    self.recv_data()
                    self.logger.info("reconnect success!")
                except:
                    #traceback.print_exc()
                    self.logger.info("reconnect failed...")
            finally:
                self.mutex.release()
                time.sleep(4)
    '''

    def login(self, user_name, password):
        '''
        check if user_name and password are correct

        Args:
            user_name: string
            password: string

        Returns:
            False or True
        '''
        data = dict()
        data["type"] = "req_login"
        data["user_name"] = user_name
        data["password"] = password
        #建立aes加密对象
        data["aes_key"], data["aes_iv"] = self.Crypto.new_aes(AES.MODE_CBC)

        self.mutex.acquire()
        #发送数据
        self.send_data(data)
        #接受服务端数据
        data_recv = self.recv_data()
        self.mutex.release()
        
        #判断是否成功登陆
        if data_recv["auth"] == "correct":
            self.user_name = user_name
            self.password = password
            #短线重连
            '''
            live_check = threading.Thread(target=self.server_live_check)
            live_check.setDaemon(True)
            live_check.start()
            '''
            return True
        else:
            return False

    def recv_data(self):
        '''
        receive data sent from server

        Returns:
            server sent data in json format
        '''
        #读取包长度并转为int
        data_len = self.sock.recv(64).decode()
        data_len = int(data_len.strip())
        #读取加密类型
        data_spec = self.sock.recv(1).decode()
        #读取包
        data_recv = b''
        while len(data_recv) != data_len:
            data_recv += self.sock.recv(data_len)
        self.logger.info("client received data_len:"+str(data_len))
        self.logger.info("client received data length:"+str(len(data_recv)))
        #aes解密
        data_recv = self.Crypto.decrypt(data_spec, data_recv)
        #print("client received (crypto removed):")
        #print(data_recv)

        if data_recv["type"] == "error":
            raise Exception("server handler error!")

        return data_recv
    
    def send_data(self, data):
        '''
        send data to server

        Args:
            data: data to send in json format
        '''
        #加密
        data_send_crypto = self.Crypto.encrypt(data)
        #计算paylod长度:
        data_len = str(len(data_send_crypto))
        data_len += ' '*(64-len(data_len))
        #specify segment
        if data["type"] == "req_login":
            data_spec = "0"
        elif data["type"] == "live_check":
            data_spec = "2"
        else:
            data_spec = "1"
        #发送
        self.sock.sendall(data_len.encode()+data_spec.encode()+data_send_crypto)
        self.logger.info("client sent:")
        self.logger.info(data_len.encode()+data_spec.encode()+data_send_crypto)
        #print(data_len + data_spec + json.dumps(data))

    def query_stock_kline(self, stock_code, start_date, end_date):
        '''
        query stock k-line data from server

        Args:
            stock_code: stock code string
            start_date: starting date string
            end_date: ending date string
        
        Returns:
            stock k-line data in DataFrame format
        '''
        data = dict()
        data["type"] = "req_stock_kline"
        data["stock_code"] = stock_code
        data["start_date"] = start_date
        data["end_date"] = end_date

        self.mutex.acquire()
        #发送数据
        self.send_data(data)
        #接受服务端数据
        data_recv = self.recv_data()
        self.mutex.release()

        return pandas.read_json(data_recv["data"], orient = "columns")

    def query_stock_detail(self, stock_code = "600519"):
        '''
        query stock detail from server

        Args:
            stock_code: stock code string
        
        Returns:
            stock detail data in list format
        '''
        data = dict()
        data["type"] = "req_stock_detail"
        data["stock_code"] = stock_code

        self.mutex.acquire()
        #发送数据
        self.send_data(data)
        #接收数据
        data_recv = self.recv_data()
        self.mutex.release()

        return json.loads(data_recv["data"])

    def query_stock_list(self):
        '''
        query stock list data from server

        Returns:
            stock list data in list format
        '''
        data = dict()
        data["type"] = "req_stock_list"

        self.mutex.acquire()
        #发送数据
        self.send_data(data)
        #接收数据
        data_recv = self.recv_data()
        self.mutex.release()

        return json.loads(data_recv["data"])
    
class LiveCheck(QThread):
    """
    LiveCheck class is responsible for checking client connection with server, and do reconnect if drop out
    """
    drop_out = pyqtSignal(list)
    reconnect_succeed = pyqtSignal(list)
    reconnect_failed = pyqtSignal(list)
    def __init__(self):
        super().__init__()
        self.client_model = ClientModel.getInstance()
    def run(self):
        '''
        check if server is alive, try reconnect dead server
        '''
        while True:
            try:
                data = dict()
                data["type"] = "live_check"
                self.client_model.mutex.acquire()
                self.client_model.send_data(data)
                self.client_model.recv_data()
                #self.client_model.logger.info("socket connection condition check: good")
            except:
                self.client_model.logger.info("socket error, try reconnect...")
                self.drop_out.emit(["error!", "connection with server drop out..."])
                fail_cnt = 0
                time.sleep(2)
                #reconnect
                while True:
                    try:
                        self.client_model.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.client_model.sock.connect((self.client_model.ip, self.client_model.port))
                        self.client_model.logger.info("reconnect success!")
                        self.reconnect_succeed.emit(["info", "reconnect succeed!"])
                        break
                    except:
                        traceback.print_exc()
                        if fail_cnt == 0:
                            self.reconnect_failed.emit(["error!", "reconnect failed!"])
                            fail_cnt += 1
                        self.client_model.logger.info("reconnect failed...")
                        time.sleep(1)
            finally:
                self.client_model.mutex.release()
                time.sleep(4)


if __name__ == "__main__":
    client = ClientModel(HOST, PORT)
    client.login("admin", "123456")
    time.sleep(100)