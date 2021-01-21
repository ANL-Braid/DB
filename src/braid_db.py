
# BRAID DB

import datetime
import logging
import os

from db_tools import BraidSQL, q, qA

def digits(c):
    ''' Return c random digits (for random names) '''
    import math, random
    n = random.randint(0, 10**c)
    s = "%0*i" % (c, n)
    return s


class BraidDB:

    def __init__(self, db_file, debug=True):

        self.logger = logging.getLogger("BraidDB")
        if debug: self.logger.setLevel(logging.DEBUG)

        self.sql = BraidSQL(db_file, log=True, debug=False)
        self.sql.connect()

    def create(self):
        ''' Set up the tables defined in the SQL file '''
        BRAID_HOME = os.getenv("BRAID_HOME")
        if BRAID_HOME == None:
            raise Exception("Set environment variable BRAID_HOME!")
        print("creating tables: ")
        braid_sql = BRAID_HOME + "/src/braid-db.sql"
        with open(braid_sql) as fp:
            sqlcode = fp.read()
            self.sql.executescript(sqlcode)
            self.sql.commit()

    def insert(self, record):
        pass

    def print(self):
        self.sql.select("records", "*");
        records = {}
        while True:
            row = self.sql.cursor.fetchone()
            if row == None: break
            (record_int, name, time) = row[0:3]
            records[record_int] = "%3i : %-16s %s" % \
                (record_int, name, time)
        for record_int in list(records.keys()):
            deps = self.get_dependencies(record_int)
            print(records[record_int] + " <- " + str(deps))

    def get_dependencies(self, record_int):
        '''
        return list of integers
        '''
        self.trace("DB.get_dependencies(%i) ..." % record_int)
        self.sql.select("dependencies", "dependency",
                        "record_int=%i" % record_int)
        deps = []
        while True:
            row = self.sql.cursor.fetchone()
            if row == None: break
            deps.append(row[0])
        return deps

    def debug(self, msg):
        self.logger.debug(msg)

    def trace(self, msg):
        self.logger.log(level=logging.DEBUG-5, msg=msg)



serial = 1

def make_serial():
    global serial
    result = serial
    serial += 1
    return result


class BraidRecord:

    def __init__(self, uri, db=None, name=None, timestamp=None, debug=True):
        self.serial = make_serial()
        self.uri = uri
        self.db = db
        self.name = name
        self.dependencies = []
        # None indicates the Record is not in the DB yet
        self.record_int = None

        self.logger = logging.getLogger("BraidRecord")
        if debug: self.logger.setLevel(logging.DEBUG)

        if timestamp == None:
            self.timestamp = datetime.datetime.now()
        else:
            self.timestamp = timestamp

    def add_dependency(self, record):
        ''' record: a BraidRecord '''
        self.dependencies.append(record)
        self.db.sql.insert("dependencies", ["record_int", "dependency"],
                           [str(self.record_int), str(record.record_int)])

    def strftime(self):
        return self.timestamp.strftime("%Y-%m-%d %H:%M:%S")

    def __str__(self):
        if self.name == None:
            return "BraidRecord(uri=%s)" % self.uri
        else:
            return "BraidRecord(\"%s\": uri=%s)" % \
                (self.name, self.uri)

    def debug(self, msg):
        self.logger.debug(msg)


class BraidFact(BraidRecord):

    ''' Examples: pre-existing data, software, etc. '''

    def __init__(self, uri, db=None, name=None):
        super().__init__(uri, db=db, name=name)

    def add_dependency(self, record):
        ''' record: a BraidRecord '''
        raise Exception("BraidFacts do not have dependencies!")

    def store(self):
        self.record_int = self.db.sql.insert("records", ["name", "time"],
                                             qA(self.name, self.strftime()))
        self.debug("stored Fact: <%s>" % self.record_int)
        return self.record_int


class BraidData(BraidRecord):

    ''' Examples: data in the system with dependencies:
        Simulation outputs, data analyses, experiment outputs
    '''

    def __init__(self, uri, db=None, name=None):
        super().__init__(uri, db=db, name=name)

    def store(self):
        self.record_int = self.db.sql.insert("records", ["name", "time"],
                                             qA(self.name, self.strftime()))
        self.debug("stored Data: <%s>" % self.record_int)
        return self.record_int


class BraidModel(BraidRecord):

    ''' Examples: an ML model that is trained on BraidRecords '''

    def __init__(self, uri, db=None, name=None):
        super().__init__(uri, db=db, name=name)

    def update(self, record):
        ''' record: a BraidRecord '''
        super().add_dependency(data)

    def store(self):
        self.record_int = self.db.sql.insert("records", ["name", "time"],
                                             qA(self.name, self.strftime()))
        self.debug("stored Model: <%s>" % self.record_int)
        return self.record_int

# class Braid
