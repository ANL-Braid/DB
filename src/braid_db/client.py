class Client:
    def __init__(self, comm):
        self.comm = comm
        self.rank = self.comm.Get_rank()

    def check(self):
        print("client: start ...")
        self.comm.send("CLIENT:%i" % self.rank, dest=0)
        msg = self.comm.recv(source=0)
        print("client: received: " + msg)
        print("client: stop ...")
