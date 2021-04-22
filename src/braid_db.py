
# BRAID DB

import datetime
import logging
import os

from db_tools import BraidSQL, q, qA


def digits(c):
    ''' Return c random digits (for random names) '''
    import random
    n = random.randint(0, 10**c)
    s = "%0*i" % (c, n)
    return s


from enum import Enum, unique


@unique
class BraidTagType(Enum):
    # Cf braid-db.sql
    NONE    = 0
    STRING  = 1
    INTEGER = 2
    FLOAT   = 3


class BraidTagValue:
    def __init__(self, value, type_):
        self.value = value
        self.type_ = type_


class BraidDB:

    def __init__(self, db_file, debug=True):

        self.logger = logging.getLogger("BraidDB")
        if debug: self.logger.setLevel(logging.DEBUG)

        self.sql = BraidSQL(db_file, log=True, debug=True)
        self.sql.connect()

    def create(self):
        ''' Set up the tables defined in the SQL file '''
        BRAID_HOME = os.getenv("BRAID_HOME")
        if BRAID_HOME is None:
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
        self.sql.select("records", "*")
        records = {}
        while True:
            row = self.sql.cursor.fetchone()
            if row is None: break
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
        self.extract_tags(records)
        for record_id in list(records.keys()):
            print(records[record_id])

    def extract_tags(self, records):
        ''' Append tags data to records '''
        for record_id in list(records.keys()):
            tags = self.get_tags(record_id)
            text = records[record_id]
        for key in tags.keys():
            text += "\n\t\t\t TAG: "
            if tags[key].type_ == BraidTagType.INTEGER or \
               tags[key].type_ == BraidTagType.FLOAT:
                text += "%s = %s"   % (key, tags[key].value)
            else:
                text += "%s = '%s'" % (key, tags[key].value)
            records[record_id] = text

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
            if row is None: break
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
            if row is None: break
            uris.append(row[0])
        return uris

    def get_tags(self, record_id):
        '''
        return dict of string->BraidTagValue key->value pairs
        '''
        self.trace("DB.get_tags(%i) ..." % record_id)
        self.sql.select("tags", "key, value, type",
                        "record_id=%i" % record_id)
        tags = {}
        while True:
            row = self.sql.cursor.fetchone()
            if row is None: break
            (key, v, t) = row[0:3]
            type_ = BraidTagType(t)
            value = BraidTagValue(v, type_)
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
        # Dict of string->BraidTagValue
        self.tags = {}
        # None indicates the Record is not in the DB yet
        self.record_id = None

        self.logger = logging.getLogger("BraidRecord")
        if debug: self.logger.setLevel(logging.DEBUG)

        if timestamp is None:
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

    def add_tag(self, key, value, type_=BraidTagType.STRING):
        ''' key:   a string key name
            value: a string value
        '''
        if not isinstance(type_, BraidTagType):
            raise Exception("type must be a BraidTagType! " +
                            "received: '%s' type: %s" % (
                                str(type_), type(type_)))
        self.tags[key] = value
        self.db.sql.insert("tags",
                           ["record_id", "key", "value", "type"],
                           [str(self.record_id),
                            q(key), q(value), str(type_.value)])

    def strftime(self):
        return self.timestamp.strftime("%Y-%m-%d %H:%M:%S")

    def __str__(self):
        if self.name is None:
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
        super().add_dependency(record)

    def store(self):
        self.record_id = self.db.sql.insert("records", ["name", "time"],
                                            qA(self.name, self.strftime()))
        self.debug("stored Model: <%s>" % self.record_id)
        return self.record_id

# class Braid
