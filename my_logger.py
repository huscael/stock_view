import logging

class MyLogger(logging.Logger):
    '''
    singleton logger
    '''
    __instance = None

    @staticmethod 
    def getInstance(filename = "debug.log"):
        """ Static access method. """
        if MyLogger.__instance == None:
            MyLogger(filename)
        return MyLogger.__instance

    def __init__(self, filename):
        """ Virtually private constructor. """
        if MyLogger.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            MyLogger.__instance = self
            super().__init__(name = "my_logger")
            self.setLevel(logging.INFO)
            #add formatter
            fmt = "%(asctime)-15s %(levelname)s %(filename)s:%(funcName)s line:%(lineno)d thread:%(threadName)s-%(thread)d\n>%(message)s"
            datefmt = "%Y-%b-%d %H:%M:%S"
            formatter = logging.Formatter(fmt, datefmt)
            #add file_handler
            file_handler = logging.FileHandler(filename=filename, mode="w")
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            self.addHandler(file_handler)
            
            with open("debug.log", "a") as f:
                f.write(">>>start logging>>>\n")

if __name__=="__main__":
    my_logger = MyLogger.getInstance()
    my_logger.info("hello world")
    my_logger.warning("warn msg")
    my_logger_2 = MyLogger.getInstance()
    print(my_logger == my_logger_2)
    print(my_logger is my_logger_2)
    my_logger_2.info("hello world 2")