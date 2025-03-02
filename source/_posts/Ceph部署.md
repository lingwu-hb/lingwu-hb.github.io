---
title: Ceph部署
date: 2025-02-03 15:19:33
categories:
- data storage
tags:
- ceph
---



# Ceph Monitor职责

1. 维护集群状态图（Cluster Map），Cluster Map为全局的元数据，包括以下信息:

- OSD Map	记录所有 OSD 节点的状态（如在线/离线）、存储容量、数据分布规则（CRUSH 算法配置）。
- MON Map	记录 Monitor 节点自身的列表和地址。
- PG Map	管理 Placement Group（PG）的映射关系（PG 是数据分片逻辑单元）。
- MDS Map（仅当使用 CephFS 时）	记录 Metadata Server 的状态。

2. 管理集群的 Paxos 共识，确保Cluster Map的强一致性。

3. 处理客户端请求
   客户端（如 RBD、RGW、CephFS）首次连接集群时，会从 Monitor 获取最新的 Cluster Map，用于确定数据的读写位置（如 OSD 地址）。客户端后续操作直接与 OSD 通信，无需持续依赖 Monitor（除非 Cluster Map 更新）。

4. 监控集群健康状态

5. 管理身份认证与权限

6. 协调 PG 状态变更

7. 处理配置变更

   ```bash
   ceph-deploy mon create-initial
   ```

# Ceph MGR职责

1. 提供集群管理和监控功能

   ```bash
   ceph-deploy mgr create <mgr-node>
   ```

2. 收集和展示集群的性能和健康状态

   ```bash
   ceph mgr module enable dashboard
   ```

3. 提供 RESTful API 接口，供外部应用程序使用

   ```bash
   ceph mgr module enable rest-api
   ```

4. 管理和协调集群的配置

   ```bash
   ceph config set mgr mgr/dashboard/server_addr <ip>:<port>
   ```

5. 处理集群的任务调度和负载均衡

   ```bash
   ceph mgr module enable balancer
   ```


# Ceph OSD职责

1. 存储数据

2. 处理数据复制、恢复、回填、再均衡

3. 维护数据完整性

4. 监控自身状态并报告给 Monitor

5. 处理客户端读写请求

   ```bash
   ceph-deploy osd create <osd-node>:<disk>
   ```

# Ceph MDS职责

1. 管理文件系统的元数据

2. 将元数据缓存到内存中，以支持高性能的文件访问

3. 维护文件系统的命名空间

4. 处理文件系统操作，如打开、关闭、读写、重命名等

5. 处理客户端请求，将元数据操作转换为底层存储操作

   ```bash
   ceph-deploy mds create <mds-node>
   ```

