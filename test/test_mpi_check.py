
from mpi4py import MPI
from server import Server
from client import Client


comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

if rank == 0:
    print("test_mpi_check ...")
    server = Server()
    server.check()
    print("test_mpi_check: OK")
else:
    client = Client()
    client.check()
