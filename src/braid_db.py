
import datetime

class BraidDB:

    def create():
        pass

    def insert():

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
        self.uri = url
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
        self.uri = url

    def add_dependency(self, record):
         raise Exception("BraidFacts do not have dependencies!")

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
