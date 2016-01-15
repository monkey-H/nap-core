###提供基本镜像

- apache docker.iwanna.xyz:5000/apache2:v1  
- mysql docker.iwanna.xyz:5000/user_mysql:v1  
- mpi docker.iwanna.xyz:5000/mpi:v1  
- maven docker.iwanna.xyz:5000/maven:v1  
- hbase docker.iwanna.xyz:5000/hbase_master:v1  docker.iwanna.xyz:5000/hbase_slave:v1


###从基本镜像启动

数据类型：　project_name list[dict{}, dict{}]  
- service_name  
- type   
- ports  
- links  
- command  
- url  
- environment  
- slaves n (mpi mapreduce, hbase特有)  


mysql 需要初始密码，environment参数里面MYSQL_ROOT_PASSWORD
