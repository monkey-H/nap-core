from orchestration import config
from orchestration.nap_api import create_from_table

def create_mpi(username, password, mpi_name, slaves):
    args = ['slaves':slaves]
    create_from_table(username, password, mpi_name, args)
