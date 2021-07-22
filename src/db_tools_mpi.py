
import logging
import sqlite3

from mpi4py import MPI
from server import Server
from client import Client


class BraidSQL_MPI:
    '''
    Sets up a wrapper around the SQL connection and cursor objects
    '''

    def __init__(self, db_file, log=False, debug=False):
        self.db_file = db_file
        self.conn = None
        self.autoclose = True

        self.comm = MPI.COMM_WORLD
        self.rank = self.comm.Get_rank()
        self.size = self.comm.Get_size()

        self.logger    = None  # Default
        # self.delay = 0.20    # For backoffs (WIP)
        if log or debug:
            fmt = "%(asctime)s %(name)-12s %(message)s"
            logging.basicConfig(format=fmt,
                                datefmt='%Y-%m-%d %H:%M:%S')
            self.logger = logging.getLogger("BraidSQL")
            if debug:
                self.logger.setLevel(logging.DEBUG)
                self.debug("debugging enabled ...")
            else:
                self.logger.setLevel(logging.INFO)

    def connect(self):
        print("connect")
        if self.rank == 0:
            self.server = Server(self.comm)
            self.conn = sqlite3.connect(self.db_file)
            self.cursor = self.conn.cursor()
            self.cursor.execute("PRAGMA busy_timeout = 1000")
            self.server.check()
            # self.conn.isolation_level = None
            # self.conn.isolation_level = "EXCLUSIVE"
        else:
            self.client = Client(self.comm)
            self.client.check()

        return "OK"

    def select(self, table, what, where=None):
        ''' Do a SQL select '''
        cmd = "select %s from %s" % (what, table)
        if where is not None:
            cmd += " where "
            cmd += where
        cmd += ";"
        self.execute(cmd)

    def insert(self, table, names, values):
        """ Do a SQL insert """
        names_tpl  = sql_tuple(names)
        values_tpl = sql_tuple(values)
        cmd = "insert into {} {} values {};"\
              .format(table, names_tpl, values_tpl)
        self.execute(cmd)
        rowid = str(self.cursor.lastrowid)
        # self.conn.commit()
        return rowid

    def execute(self, cmd):
        self.debug(cmd)
        self.cursor.execute(cmd)
        # import random
        # import time
        # while True:
        #     try:
        #         self.cursor.execute(cmd)
        #         self.delay *= 0.9
        #         break
        #     except Exception as e:
        #         self.log(str(e))
        #         self.log("delay=%7.3f" % self.delay)
        #         time.sleep(self.delay * random.random())
        #         self.delay *= 4 * random.random()

    def executescript(self, cmds):
        self.cursor.executescript(cmds)

    def commit(self):
        self.conn.commit()

    def close(self):
        print("transaction: %b" % self.conn.in_transaction)
        self.autoclose = False
        self.conn.close()

    def log(self, message):
        if self.logger:
            self.logger.info(message)

    def debug(self, message):
        if self.logger:
            self.logger.debug(message)

    def __del__(self):
        self.debug("BraidSQL del()")
        if not self.autoclose:
            return
        if self.conn is None:
            self.debug("No connection!")
            return
        self.debug("transaction: %r" % self.conn.in_transaction)
        self.conn.commit()
        self.conn.close()
        self.log("DB auto-closed.")


def q(s):
    """ Quote the given string """
    return "'" + str(s) + "'"


def qL(L):
    """ Quote each list entry as a string """
    return map(q, L)


def qA(*args):
    """ Quote each argument as a string """
    return map(q, args)


def sql_tuple(L):
    """ Make the given list into a SQL-formatted tuple """
    result = ""
    result += "("
    result += ",".join(L)
    result += ")"
    return result
