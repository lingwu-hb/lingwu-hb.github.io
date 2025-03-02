---
title: ceph
date: 2024-06-02 16:02:26
categories:
tags:
---





## IO读写流程

1. 检查OSD的状态，以及epoch是否一致
2. 完成对PG的状态、对象的状态的检查、并将请求封装成事务
3. 把封装好的事务通过网络分发到从副本上，最后调用本地FileStore完成本地数据的写入



## 问题

1. 怎么理解pg_pool_t的replication和ErasureCode两种模式



## 后续学习内容

1. 操作系统实验文件系统
2. ？

## 学习方法

从哪里下手进行学习 》 IO路径流程
