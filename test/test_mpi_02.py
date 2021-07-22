
from mpi4py import MPI
from server import Server
from client import Client

from braid_db import BraidDB


comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()


def test_server():
    pass

def test_client():
    pass


if rank == 0:
    print("check ...")
    server = Server(comm)
    server.check()
    print("check: OK")
    test_server()
else:
    client = Client(comm)
    client.check()
    test_client()

DB = BraidDB("braid.db", mpi=True)
DB.create()
