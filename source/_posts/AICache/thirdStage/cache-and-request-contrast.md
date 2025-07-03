---
title: cache and request contrast
date: 2025-07-03 09:20:11
categories:
- data storage
tags:
- ocf
---



# 说明

本文主要分析 ocf 和 tsprefetchus 中的 cache 和 request 数据差异

代码地址：

ocf：https://github.com/lingwu-hb/ModifiedOCF

tsprefetchus：https://github.com/lingwu-hb/libCacheSim



# cache

## ocf

| struct ocf_cache_device* device; | 指向缓存设备结构体，包含缓存设备的相关信息<br />查缓存基本都是靠 device |
| -------------------------------- | ------------------------------------------------------------ |
| struct list_head list;           | 链表头，用于将缓存实例链接到全局缓存列表中                   |
| struct list_head io_queues;      | I/O队列链表，管理I/O请求队列                                 |
| struct ocf_metadata metadata;    | 缓存元数据                                                   |
| unsigned long cache_state;       | 缓存状态标志，控制缓存是否接受IO请求                         |
|                                  |                                                              |
|                                  |                                                              |
|                                  |                                                              |
|                                  |                                                              |
|                                  |                                                              |

ocf_cache 数据结构：管理缓存设备、核心设备、元数据、I/O请求以及各种缓存策略。





## tspre

| struct hashtable *hashtable;             | 哈希表指针，用于快速查找缓存中的对象                |
| ---------------------------------------- | --------------------------------------------------- |
| 各种函数指针                             | get, find, insert, evict 等等缓存操作               |
| prefetcher_t *prefetcher;                | 该 cache 对应的 预取器                              |
| int64_t n_req;                           | 请求的数量，部分淘汰算法需要用到该参数              |
| int64_t n_obj;                           | 缓存中对象的数量（应通过 get_n_obj 函数访问）       |
| int64_t occupied_byte;                   | 已占用的字节数（应通过 get_occupied_byte 函数访问） |
| int64_t cache_size;                      | 缓存大小（字节）                                    |
| int64_t default_ttl;                     | 对象默认生存时间                                    |
| int32_t obj_md_size;                     | 对象元数据大小                                      |
| char cache_name[CACHE_NAME_ARRAY_LEN];   | 缓存名称                                            |
| char init_params[CACHE_INIT_PARAMS_LEN]; | 初始化参数                                          |





# request

## ocf

### 核心IO信息（最基础必需的）

1. byte_position - 请求的起始地址

1. byte_length - 请求的长度

1. rw - 读写方向

1. data - 请求数据指针

### 缓存管理必要字段（对缓存系统至关重要）

1. cache 和 core - 缓存和核心设备句柄

1. core_line_first/core_line_last/core_line_count - 缓存行映射信息

1. cache_mode - 缓存模式

1. part_id - 分区ID

1. dirty - 脏数据标记

1. map - 缓存映射信息

### 请求状态和控制（请求生命周期管理）

1. ref_count - 引用计数

1. req_remaining - 剩余IO操作数

1. error - 错误状态

1. complete - 完成回调

1. io_queue - IO队列句柄

### 锁定和并发控制

1. lock_remaining - 待锁定缓存行数

1. alock_status - 锁状态映射

1. alock_rw - 锁读写模式

1. lock_idx - 元数据锁索引

### 缓存策略相关（影响缓存决策）

1. force_pt - 强制直通

1. allow_second_admission - 二次准入控制

1. part_evict - 分区驱逐标记

1. seq_cutoff - 顺序截断标记

### 性能优化和跟踪

1. timestamp - 时间戳

1. sid - 序列ID

1. cp_data - 数据副本（用于某些优化场景）

### 内部实现细节（相对边缘）

1. ioi - 内部IO结构

1. engine_cbs - 引擎回调

1. io_if - IO接口

1. priv - 私有数据

1. master_io_req - 主IO请求

1. master_io_req_type - 主请求类型

1. master_remaining - 主设备计数器

1. list - 链表节点

1. discard - 丢弃信息



## tspre

### 核心字段

- clock_time: 请求的时间戳

- obj_id: 对象ID，标识请求的对象

- obj_size: 对象大小

- op: 请求操作类型

- hv: 哈希值，用于卸载哈希到读取器

- valid: 表示请求是否有效

### 重要但非核心字段

- ttl: 生存时间

- n_req: 请求计数

- next_access_vtime: 下次访问的虚拟时间

- eviction_algo_data: 驱逐算法数据

- key_size/val_size: 键值大小

### 元数据/分类字段

- ns: 命名空间

- content_type: 内容类型

- tenant_id: 租户ID

- bucket_id: 桶ID

### 分析用途字段

- vtime_since_last_access: 自上次访问以来的虚拟时间

- rtime_since_last_access: 自上次访问以来的实际时间

- prev_size: 之前的大小

- create_rtime: 创建时间

- compulsory_miss: 是否为强制缺失

- overwrite: 是否覆盖之前的对象

- first_seen_in_window: 在时间窗口内首次看到

### 边缘字段

- age: 年龄

- hostname: 主机名

- extension: 扩展

- colo: 托管位置

- n_level/n_param: 级别和参数数量

- method: 方法

- prefetch_flag: 预取标志

- trigger_block: 触发预取的块

- offset_end: 标记是否有偏移量结束



# ocf 缺少的信息

1. cache->prefetcher->params

初始化预取器的参数，后续操作的时候需要提取预取器参数信息

2. req->trigger_block 和 req->prefetch_flag 字段

是否为预取进入缓存，触发预取操作的对象



TODO：另外两种专家预取器执行操作的时候需要哪些内容，OCF 是否能够提供？
