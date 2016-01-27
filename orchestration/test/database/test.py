from orchestration.database import database_update

#print database_update.machine_ip('wangwy', 'wangwy', 'cdh', 'slave1')
#print database_update.machine_ip('wangwy', 'wangwy', 'cdh', 'master')
#print database_update.machine_ip('wangwy', 'wangwy', 'cdh', 'cloudera_manager')

print database_update.machine_ip('mongo', 'mongo', 'test', 'web')
