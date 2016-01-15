from orchestration.nap_api import create_from_table

ll = [{'service_name':'aa', 'type':'apache', 'command':'hello', 'ports':[123,45]}, {'service_name':'aa', 'type':'mpi', 'slaves':4} ]
print create_from_table.create_project_from_table("mongo", 'mongo', 'table', ll)
