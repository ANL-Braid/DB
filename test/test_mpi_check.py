from mpi4py import MPI

from client import Client
from server import Server

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

if rank == 0:
    print("test_mpi_check ...")
    server = Server(comm)
    server.check()
    print("test_mpi_check: OK")
else:
    client = Client(comm)
    client.check()
