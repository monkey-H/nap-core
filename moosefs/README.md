

moosefs组件，用来整合存储资源。


在集群中的每台机器上build　chunkserver容器，在某一台机器上build master容器，某一台机器上build metalogger组件，分别运行。

启动之后，注意修改moosefs 组件的/etc/hosts文件，添加mfsmaster的ｉｐ信息，此ｉｐ即为moosefs master容器的ｉｐ。

注意启动moosefs容器的时候，需要使用--net host 启动，因为我们需要所有的容器均可访问，所以有个所有容器可访问的ｉｐ是必须的。

docker run -tid --name chunkserver --net host -v /moosefs_data/:/moosefs mfs_chunkserver bash
docker run -tid --name mfs_master --net host mfs_master bash
