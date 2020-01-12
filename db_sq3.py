import sqlite3 as sq3

class db:
    def __init__(self,db_name):
        self.conn = sq3.connect(db_name)
        self.cur = self.conn.cursor()

    def create_user_table(self):
        sql = '''
        create table if not exists users(
            user_name varchar primary key,
            password varchar)
        '''
        self.cur.execute(sql)
        self.conn.commit()
    
    def create_stockDetail_table(self):
        sql = '''
        create table if not exists stockDetail(
            time varchar primary key,
            current_price double,
            total_turnover double,
            amount int)
        '''
        self.cur.execute(sql)
        self.conn.commit()

    def create_stockList_table(self):
        sql = '''
        create table if not exists stockList(
            ord int primary key,
            code varchar,
            name varchar, 
            yesterday_closing_price double,
            yesterday_settlement_price double,
            held_amound long,
            harden_price double,
            dropstop_price double,
            total_stock long,
            circulation long,
            contract_quantity_mutiplier int,
            min_change_price double,
            date varchar)
        '''
        self.cur.execute(sql)
        self.conn.commit()

    def drop_table(self, table_name):
        sql = '''
        drop table {}
        '''.format(table_name)
        self.cur.execute(sql)
        self.conn.commit()

    def read_all(self,table_name):
        sql = '''
        select * from {}
        '''.format(table_name)
        self.cur.execute(sql)
        return self.cur.fetchall()
    
    def insert_user(self,user_name, password):
        sql = '''
        insert into users values(
            '{}', '{}')
        '''.format(user_name, password)
        self.cur.execute(sql)
        self.conn.commit()

    def clear(self,table_name):
        sql = '''
        delete from {}
        '''.format(table_name)
        self.cur.execute(sql)
        self.conn.commit()

    def check_user(self, user_name, password):
        sql = '''
        select * from users
        where
        user_name = '{}'
        '''.format(user_name)
        results = self.cur.execute(sql).fetchall()
        if len(results) == 0 :
            return False
        elif results[0][1]!=password :
            return False
        return True
    
    def build_stockDetail(self):
        self.clear("stockDetail")
        with open("stock.txt", "r") as f:
            for i, line in enumerate(f.readlines()):
                if i>0:
                    line = line.split('\t')[0:4]
                    sql = '''
                    insert into stockDetail values(
                        '{}', {}, {}, {})
                    '''.format(*line)
                    self.cur.execute(sql)
                    self.conn.commit()

    def build_stockList(self):
        self.clear("stockList")
        with open("stock_list.txt", "r") as f:
            for i, line in enumerate(f.readlines()):
                line = line.split('\t')[0:13]
                sql = '''
                insert into stockList values(
                    {}, '{}', '{}', {}, {}, {}, {}, {}, {}, {}, {}, {}, '{}')
                '''.format(*line)
                self.cur.execute(sql)
                self.conn.commit()


if __name__=='__main__':
    x = db('test.db')
    x.create_stockList_table()
    x.build_stockList()
    print(x.read_all("stockList"))
