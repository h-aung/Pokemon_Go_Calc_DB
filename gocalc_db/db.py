import sqlite3
import numpy as np
sqlite3.register_adapter(np.int64, int)

class database(object):
    __cur__=None
    __dbopen__=False
    __conn__=None
    __print__=False

    def init_database(self, name=None):
        if self.__dbopen__:
            self.close_database()
        if name==None:
            name='data/example.db'
        self.__conn__ = sqlite3.connect(name)
        self.__cur__ = self.__conn__.cursor()
        print("    Database established!!!")
        self.__dbopen__=True
        return
        
    def close_database(self):
        if self.__dbopen__:
            self.__conn__.commit()
            self.__conn__.close()
        print( "    Previous database closed!!!")
        self.__dbopen__=False
        return
    
    def test_database(self):
        self.__cur__.execute("PRAGMA table_info(pokemon)")
        print( "    Testing (id=%s)!!!"%(self.__cur__.fetchone()[1]))
        return
        
    def turn_on_statement(self):
        if self.__print__:
            self.__conn__.set_trace_callback(None)
            self.__print__=False
        else:
            self.__conn__.set_trace_callback(print)
            self.__print__=True
        return
        
    def explore(self,sql_statement):
        if not sql_statement.startswith('SELECT'):
            print( "    Your SQL statement must start with 'SELECT'!!!")
            return None
        self.__cur__.execute(sql_statement)
        return self.__cur__.fetchall()
        
DB = database()