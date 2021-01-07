
import sqlite3

class BraidSQL:
    '''
    Sets up a wrapper around the SQL connection and cursor objects
    '''

    def __init__(self, db_file, log=False):
        self.db_file   = db_file
        self.conn = None
        self.autoclose = True
        self.logger    = None # Default
        if log:
            logging.basicConfig(format="SQL: %(message)s")
            self.logger = logging.getLogger("BraidSQL")
            self.logger.setLevel(logging.DEBUG)

    def connect(self):
        self.conn = sqlite3.connect(self.db_file)
        self.cursor = self.conn.cursor()
        self.cursor.execute("PRAGMA busy_timeout = 1000")
        return "OK"

    def insert(self, table, names, values):
        """ Do a SQL insert """
        names_tpl  = sql_tuple(names)
        values_tpl = sql_tuple(values)
        cmd = "insert into {} {} values {};"\
              .format(table, names_tpl, values_tpl)
        self.execute(cmd)
        rowid = str(self.cursor.lastrowid)
        return rowid

    def execute(self, cmd):
        self.log(cmd)
        self.cursor.execute(cmd)

    def executescript(self, cmds):
        self.cursor.executescript(cmds)

    def commit(self):
        self.conn.commit()

    def close(self):
        self.autoclose = False
        self.conn.close()

    def log(self, message):
        if self.logger:
            self.logger.info(message)

    def __del__(self):
        if not self.autoclose:
            return
        if self.conn == None:
            return
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
