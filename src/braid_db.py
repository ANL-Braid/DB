
import datetime
import os

from db_tools import BraidSQL, qA

def setup_db(db_file):
    '''
    Convenience function to use from workflow
    '''
    if 'DB' not in globals():
        print('Connecting to DB...')
        global DB
        DB = BraidSQL(db_file, log=True)
    return DB

class BraidDB:

    def __init__(self):
        self.DB = None

    def create(self):
        ''' Set up the tables defined in the SQL file '''
        BRAID_HOME = os.getenv("BRAID_HOME")
        if BRAID_HOME == None:
            raise Exception("Set environment variable BRAID_HOME!")
        print("creating tables: ")
        global DB
        self.DB = DB
        DB.connect()
        braid_sql = BRAID_HOME + "/src/braid-db.sql"
        with open(braid_sql) as fp:
            sqlcode = fp.read()
            DB.executescript(sqlcode)
            DB.commit()

    def insert(self, record):
        pass

serial = 1

def make_serial():
    global serial
    result = serial
    serial += 1
    return result

class BraidRecord:

    def __init__(self, uri, name=None, timestamp=None):
        self.serial = make_serial()
        self.uri = uri
        self.name = name
        self.dependencies = []
        if timestamp == None:
            self.timestamp = datetime.now()
        else:
            self.timestamp = timestamp

    def add_dependency(self, record):
        self.dependencies.append(record)

    def __str__(self):
        if self.name == None:
            return "BraidRecord(uri=%s)" % self.url
        else:
            return "BraidRecord(\"%s\": uri=%s)" % \
                (self.name, self.uri)

class BraidFact(BraidRecord):

    ''' Examples: pre-existing data, software, etc. '''

    def __init__(self, uri, name=None):
        self.uri = uri
        self.name = name

    def add_dependency(self, record):
         raise Exception("BraidFacts do not have dependencies!")

    def store(self, db):
        record_int = db.DB.insert("records", ["name", "time"], qA(self.name, "now"))
        print(record_int)

class BraidData(BraidRecord):

    ''' Examples: data in the system with dependencies:
        Simulation outputs, data analyses, experiment outputs
    '''

    def __init__(self, uri, name=None):
        self.uri = url
        self.name = name

class BraidModel(BraidRecord):

    ''' Examples: an ML model that is trained on BraidRecords '''

    def __init__(self, uri, name=None):
        self.uri = url
        self.name = name

    def update(self, data):
        self.dependencies.append(data)

# class Braid
