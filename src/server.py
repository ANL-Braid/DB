
from mpi4py import MPI


class Server:

    def __init__(self):
        self.comm = MPI.COMM_WORLD
        # rank = comm.Get_rank()
        self.size = self.comm.Get_size()
        self.workers = self.size - 1

    def check(self):
        print("server: start ...")
        count = self.workers
        while count > 0:
            status = MPI.Status()
            msg = self.comm.recv(source=MPI.ANY_SOURCE,
                                 tag=MPI.ANY_TAG,
                                 status=status)
            client = status.Get_source()
            print("server: received from %i: '%s'" % (client, msg))
            self.comm.send("OK",  dest=client)
            count -= 1
        print("server: stop ...")
