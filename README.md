
nap-core　跨主机多容器应用编排和部署方案。

database 数据库组件，使用mysql数据库容器，用来存储用户基本信息，应用列表等信息。

health_check 健康检查组件，循环遍历宿主机的容器状态信息，并且存储在分布式存储服务consul中，为之后的高可用等预留接口。

log 日志收集组件，用来收集用户部署日志和应用容器打印日志，进而做进一步的分析。

moosefs 分布式存储组件，用来统一化管理集群中各个主机的存储空间，高效利用。

orchestration 容器编排和部署控制组件，通过改写docker compose源码，实现多容器应用的跨主机部署。

security_certificate 安全认证组件，通过ldap，实现用户的认证管理。


###环境搭建    
集群主机操作系统要求１４．０４，kernel版本号》＝３．１６    

+ 安装consul，配置consul集群。    

    wget https://releases.hashicorp.com/consul/0.6.0/consul_0.6.0_linux_amd64.zip      
    unzip consul_*      
    sudo mv consul /usr/local/bin    

    master节点：    
    consul agent -server -bootstrap-expect 1 -data-dir /tmp/consul -bind=192.168.0.218 -client=192.168.0.218 &    

    slave节点:    
    consul agent -data-dir /tmp/consul -bind=192.168.0.219 -client=192.168.0.219 &    
    consul join --rpc-addr=192.168.0.219:8400 192.168.0.218    

    验证    
    consul members --rpc-addr=192.168.0.218:8400    

+ 修改docker 参数    
    更新最新的docker    
    sudo apt-get upgrade docker-engine    
    把docker加到sudo权限组里面    
    sudo user mod -aG docker {username}    
    修改docker 参数    
    DOCKER_OPTS="    
    -H unix:///var/run/docker.sock    
    -H tcp://0.0.0.0:2376    
    --cluster-store=consul://{host_ip}:8500    
    --cluster-advertise=em1:2376    

    sudo service docker restart    

    验证：    
    docker network create -d overlay test    
    host1:    
    sudo docker run -tid —name t1 —net test busy box /bin/sh    
    host2:    
    sudo docker run -tid —name t2 —net test busy box /bin/sh    
    看看能不能ping通    

+ 在一台作为与客户交互的控制端，要做以下配置。        

    git clone git@lab.artemisprojects.org:zhongliangyuan/nap-compose.git    
    cd nap-compose    
    sudo python setup.py Install    

+ 部署moosefs    

    sudo mkdir /moosefs_data    

    host master:    
    docker run -tid --name chunkserver --net host -v /moosefs_data/:/moosefs mfs_chunkserver bash    
    docker run -tid --name mfs_master --net host mfs_master bash    

    host slave    
    docker run -tid --name chunkserver --net host -v /moosefs_data/:/moosefs mfs_chunkserver bash    

    修改/etc/hosts（三个都要）    
    启动moosefs    
    192.168.0.218     mfsmaster    

    /etc/init.d/moosef-master start    

    chown -R mis:mis /moosefs    

    /etc/init.d/moosefs-chunkserver start    

    验证：    
    docker exec -ti mis_master bash    
    mfscli -SCS    

    另外，宿主机上，安装moosefs-client    

    wget -O - http://ppa.moosefs.com/moosefs.key | sudo apt-key add -    
    echo "deb http://ppa.moosefs.com/stable/apt/ubuntu/trusty trusty main" > /etc/apt/sources.list.d/moosefs.list    
    apt-get update    
    apt-get install moosefs-client    

+ 安装orchestration    

    wget https://bootstrap.pypa.io/get-pip.py    
    sudo python get-pip.py    

    git clone https://github.com/docker/compose    
    cd compose    
    sudo python setup.py install    
    sudo pip install packaging
