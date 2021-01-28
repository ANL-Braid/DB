
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
            (record_id, name, time) = row[0:3]
            text = "%3i : %-16s %s" % (record_id, name, time)
            records[record_id] = text
        for record_id in list(records.keys()):
            deps = self.get_dependencies(record_id)
            text = records[record_id] + " <- " + str(deps)
            records[record_id] = text
        for record_id in list(records.keys()):
            uris = self.get_uris(record_id)
            text = records[record_id]
            for uri in uris:
                text += "\n\t\t\t URI: "
                text += uri
            records[record_id] = text
        for record_id in list(records.keys()):
            tags = self.get_tags(record_id)
            text = records[record_id]
            for key in tags.keys():
                text += "\n\t\t\t TAG: "
                text += "%s = '%s'" % (key, tags[key])
            records[record_id] = text

        for record_id in list(records.keys()):
            print(records[record_id])

    def get_dependencies(self, record_id):
        '''
        return list of integers
        '''
        self.trace("DB.get_dependencies(%i) ..." % record_id)
        self.sql.select("dependencies", "dependency",
                        "record_id=%i" % record_id)
        deps = []
        while True:
            row = self.sql.cursor.fetchone()
            if row == None: break
            deps.append(row[0])
        return deps

    def get_uris(self, record_id):
        '''
        return list of string URIs
        '''
        self.trace("DB.get_uris(%i) ..." % record_id)
        self.sql.select("uris", "uri",
                        "record_id=%i" % record_id)
        uris = []
        while True:
            row = self.sql.cursor.fetchone()
            if row == None: break
            uris.append(row[0])
        return uris

    def get_tags(self, record_id):
        '''
        return map of string-string key-value pairs
        '''
        self.trace("DB.get_tags(%i) ..." % record_id)
        self.sql.select("tags", "key, value",
                        "record_id=%i" % record_id)
        tags = {}
        while True:
            row = self.sql.cursor.fetchone()
            if row == None: break
            (key, value) = row[0:2]
            tags[key] = value
        return tags

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

    def __init__(self, db=None, name=None, timestamp=None, debug=True):
        self.serial = make_serial()
        self.db = db
        self.name = name
        self.dependencies = []
        self.uris = []
        self.tags = {}
        # None indicates the Record is not in the DB yet
        self.record_id = None

        self.logger = logging.getLogger("BraidRecord")
        if debug: self.logger.setLevel(logging.DEBUG)

        if timestamp == None:
            self.timestamp = datetime.datetime.now()
        else:
            self.timestamp = timestamp

    def add_dependency(self, record):
        ''' record: a BraidRecord '''
        self.dependencies.append(record)
        self.db.sql.insert("dependencies", ["record_id", "dependency"],
                           [str(self.record_id), str(record.record_id)])

    def add_uri(self, uri):
        ''' uri: a string URI '''
        self.uris.append(uri)
        self.db.sql.insert("uris", ["record_id", "uri"],
                           [str(self.record_id), q(uri)])

    def add_tag(self, key, value):
        ''' key:   a string key name
            value: a string value
        '''
        self.tags[key] = value
        self.db.sql.insert("tags", ["record_id", "key", "value"],
                           [str(self.record_id), q(key), q(value)])

    def strftime(self):
        return self.timestamp.strftime("%Y-%m-%d %H:%M:%S")

    def __str__(self):
        if self.name == None:
            return "BraidRecord" % self.uri
        else:
            return "BraidRecord(\"%s\")" % self.name

    def debug(self, msg):
        self.logger.debug(msg)


class BraidFact(BraidRecord):

    ''' Examples: pre-existing data, software, etc. '''

    def __init__(self, db=None, name=None):
        super().__init__(db=db, name=name)

    def add_dependency(self, record):
        ''' record: a BraidRecord '''
        raise Exception("BraidFacts do not have dependencies!")

    def store(self):
        self.record_id = self.db.sql.insert("records", ["name", "time"],
                                             qA(self.name, self.strftime()))
        self.debug("stored Fact: <%s>" % self.record_id)
        return self.record_id


class BraidData(BraidRecord):

    ''' Examples: data in the system with dependencies:
        Simulation outputs, data analyses, experiment outputs
    '''

    def __init__(self, db=None, name=None):
        super().__init__(db=db, name=name)

    def store(self):
        self.record_id = self.db.sql.insert("records", ["name", "time"],
                                             qA(self.name, self.strftime()))
        self.debug("stored Data: <%s>" % self.record_id)
        return self.record_id


class BraidModel(BraidRecord):

    ''' Examples: an ML model that is trained on BraidRecords '''

    def __init__(self, db=None, name=None):
        super().__init__(db=db, name=name)

    def update(self, record):
        ''' record: a BraidRecord '''
        super().add_dependency(data)

    def store(self):
        self.record_id = self.db.sql.insert("records", ["name", "time"],
                                             qA(self.name, self.strftime()))
        self.debug("stored Model: <%s>" % self.record_id)
        return self.record_id

# class Braid
