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

```c
struct ocf_cache {
    struct ocf_cache_device* device;	// <1> 管理物理存储部分
    struct ocf_metadata metadata;		// <2> 缓存元数据管理
    struct list_head io_queues;			// <3> 用于特定缓存内的IO队列管理，支持多队列IO处理机制
    // ...
};
```



```c
struct ocf_cache_device {
    struct ocf_volume volume;

    /* Hash Table contains contains pointer to the entry in
     * Collision Table so it actually contains collision Table
     * indexes.
     * Invalid entry is collision_table_entries.
     */
    unsigned int hash_table_entries;
    unsigned int collision_table_entries;

    int metadata_error;
    /*!< This field indicates that an error during metadata IO
     * occurred
     */

    uint64_t metadata_offset;

    struct {
        struct ocf_alock* cache_line;
    } concurrency;

    struct ocf_superblock_runtime* runtime_meta;
};
```





## tspre



| 分类               | 字段名                        | 类型                            | 作用                                                         |
| ------------------ | ----------------------------- | ------------------------------- | ------------------------------------------------------------ |
| **核心字段**       | hashtable                     | struct hashtable*               | 哈希表指针，用于存储和管理缓存对象的键值映射。               |
|                    | cache_size                    | int64_t                         | 缓存总大小（字节），限制缓存的存储容量。                     |
|                    | default_ttl                   | int64_t                         | 默认生存时间（TTL），指定缓存对象的生命周期。                |
|                    | obj_md_size                   | int32_t                         | 对象元数据大小，用于计算缓存对象占用的额外空间。             |
|                    | cache_name                    | char[CACHE_NAME_ARRAY_LEN]      | 缓存名称，用于标识缓存实例，便于调试或管理。                 |
|                    | init_params                   | char[CACHE_INIT_PARAMS_LEN]     | 缓存初始化参数，存储配置信息。                               |
| **缓存管理字段**   | admissioner                   | admissioner_t*                  | 准入控制器指针，管理缓存对象的准入策略。                     |
|                    | **prefetcher** （需要增加的） | prefetcher_t*                   | 预取器指针，管理数据预取策略以优化性能。                     |
|                    | eviction_params               | void*                           | 驱逐策略参数，存储特定驱逐算法的配置数据。                   |
|                    | n_req                         | int64_t                         | 请求计数，记录缓存的总请求数，某些驱逐算法使用（如 LFU）。   |
|                    | to_evict_candidate            | cache_obj_t*                    | 待驱逐候选对象，确保下次驱逐时使用相同的候选对象。           |
|                    | to_evict_candidate_gen_vtime  | int64_t                         | 候选对象生成时的虚拟时间，防止使用过期的候选对象。           |
| **统计和跟踪字段** | n_obj                         | int64_t                         | 缓存对象数量（私有字段），通过 get_n_obj 访问，跟踪缓存占用情况。 |
|                    | occupied_byte                 | int64_t                         | 缓存已占用字节数（私有字段），通过 get_occupied_byte 访问，管理内存。 |
|                    | last_request_metadata         | void*                           | 最后请求的元数据，记录最近请求的上下文信息。                 |
|                    | log_eviction_age_cnt          | int64_t[EVICTION_AGE_ARRAY_SZE] | 驱逐年龄计数数组，记录对象驱逐时的年龄分布，用于分析。       |



# request

## ocf

| 分类                 | 字段                   | 作用                                             |
| -------------------- | ---------------------- | ------------------------------------------------ |
| **核心 IO 信息**     | byte_position          | 请求的起始地址，指定 IO 操作的起始位置。         |
|                      | byte_length            | 请求的长度，定义 IO 操作的数据范围。             |
|                      | rw                     | 读写方向，指示操作是读取还是写入。               |
|                      | data                   | 请求数据指针，指向待读写的数据缓冲区。           |
| **缓存管理必要字段** | cache                  | 缓存设备句柄，用于访问缓存系统。                 |
|                      | core                   | 核心设备句柄，关联底层存储设备。                 |
|                      | core_line_first        | 缓存行映射的起始行，用于定位缓存行范围。         |
|                      | core_line_last         | 缓存行映射的结束行，定义缓存行范围的结束。       |
|                      | core_line_count        | 缓存行数量，记录映射的缓存行总数。               |
|                      | cache_mode             | 缓存模式（如写回、写穿），决定缓存行为。         |
|                      | part_id                | 分区 ID，标识数据所属的分区，便于分区管理。      |
|                      | dirty                  | 脏数据标记，指示缓存数据是否已修改未同步。       |
|                      | map                    | 缓存映射信息，记录缓存与底层存储的映射关系。     |
| **请求状态和控制**   | ref_count              | 引用计数，跟踪请求的引用次数，防止提前释放。     |
|                      | req_remaining          | 剩余 IO 操作数，记录未完成的子操作数量。         |
|                      | error                  | 错误状态，记录 IO 操作的错误信息。               |
|                      | complete               | 完成回调，定义 IO 操作完成后的回调函数。         |
|                      | io_queue               | IO 队列句柄，管理请求的排队和调度。              |
| **锁定和并发控制**   | lock_remaining         | 待锁定缓存行数，跟踪尚未获取锁的缓存行数量。     |
|                      | alock_status           | 锁状态映射，记录缓存行的锁定状态。               |
|                      | alock_rw               | 锁读写模式，指定锁是用于读还是写操作。           |
|                      | lock_idx               | 元数据锁索引，用于定位锁定的元数据。             |
| **缓存策略相关**     | force_pt               | 强制直通，控制是否绕过缓存直接访问底层存储。     |
|                      | allow_second_admission | 二次准入控制，决定是否允许数据再次进入缓存。     |
|                      | part_evict             | 分区驱逐标记，指示是否需要驱逐某分区的数据。     |
|                      | seq_cutoff             | 顺序截断标记，用于优化顺序 IO 处理。             |
| **性能优化和跟踪**   | timestamp              | 时间戳，记录请求发起或处理的时间，用于性能分析。 |
|                      | sid                    | 序列 ID，唯一标识请求，便于跟踪和调试。          |
|                      | cp_data                | 数据副本，用于特定优化场景（如预读或快照）。     |
| **内部实现细节**     | ioi                    | 内部 IO 结构，存储底层的 IO 操作细节。           |
|                      | engine_cbs             | 引擎回调，定义缓存引擎的回调函数集合。           |
|                      | io_if                  | IO 接口，抽象 IO 操作的接口层。                  |
|                      | priv                   | 私有数据，存储特定实现的私有信息。               |
|                      | master_io_req          | 主 IO 请求，关联上层主请求，协调子请求。         |
|                      | master_io_req_type     | 主请求类型，标识主请求的操作类型。               |
|                      | master_remaining       | 主设备计数器，跟踪主设备未完成的 IO 操作数。     |
|                      | list                   | 链表节点，用于将请求加入队列或链表管理。         |
|                      | discard                | 丢弃信息，记录需要丢弃的数据或操作信息。         |





## tspre

| 分类                 | 字段                    | 作用                                                         |
| -------------------- | ----------------------- | ------------------------------------------------------------ |
| **核心字段**         | clock_time              | 请求的时间戳，记录请求发起的实际时间。                       |
|                      | obj_id                  | 对象 ID，唯一标识请求的目标对象。                            |
|                      | obj_size                | 对象大小，记录对象的存储空间需求。                           |
|                      | op                      | 请求操作类型（如 GET、SET、DELETE），定义操作行为。          |
|                      | hv                      | 哈希值，用于快速定位或卸载哈希到读取器。                     |
|                      | valid                   | 表示请求是否有效，用于过滤无效或已取消的请求。               |
| **重要但非核心字段** | ttl                     | 生存时间，指定缓存对象的生命周期，过期后自动失效。           |
|                      | n_req                   | 请求计数，记录对象的请求次数，用于频率分析。                 |
|                      | next_access_vtime       | 下次访问的虚拟时间，用于预测访问模式或驱逐策略。             |
|                      | eviction_algo_data      | 驱逐算法数据，存储特定驱逐算法（如 LRU、LFU）所需的元信息。  |
|                      | key_size/val_size       | 键值大小，记录键和值的存储空间占用，便于内存管理。           |
| **元数据/分类字段**  | ns                      | 命名空间，用于区分不同的数据集合或上下文。                   |
|                      | content_type            | 内容类型，标识对象的数据格式（如 JSON、图像等）。            |
|                      | tenant_id               | 租户 ID，标识请求所属的租户，支持多租户隔离。                |
|                      | bucket_id               | 桶 ID，标识对象所属的存储桶，便于分区管理。                  |
| **分析用途字段**     | vtime_since_last_access | 自上次访问以来的虚拟时间，用于分析访问间隔或优化驱逐。       |
|                      | rtime_since_last_access | 自上次访问以来的实际时间，用于性能分析或日志记录。           |
|                      | prev_size               | 之前的大小，记录对象在更新前的存储空间，用于比较或优化。     |
|                      | create_rtime            | 创建时间，记录对象首次缓存的时间，用于生命周期管理。         |
|                      | compulsory_miss         | 是否为强制缺失，标记是否因策略或错误导致缓存未命中。         |
|                      | overwrite               | 是否覆盖之前的对象，指示是否更新已有缓存数据。               |
|                      | first_seen_in_window    | 在时间窗口内首次看到，标记对象在特定时间段内的首次访问。     |
| **边缘字段**         | age                     | 年龄，记录对象在缓存中的存留时间，可能用于老化策略。         |
|                      | hostname                | 主机名，标识请求来源的主机，便于调试或分区。                 |
|                      | extension               | 扩展，记录对象的文件扩展名（如 .jpg、.txt），辅助内容分类。  |
|                      | colo                    | 托管位置，标识数据存储的物理位置（如数据中心），用于分布式系统。 |
|                      | n_level/n_param         | 级别和参数数量，存储分层缓存或其他参数化配置信息。           |
|                      | method                  | 方法，记录请求的特定方法（如 HTTP 方法），用于协议支持。     |
|                      | **prefetch_flag**       | 预取标志，指示是否触发数据预取以优化性能。                   |
|                      | **trigger_block**       | 触发预取的块，记录触发预取的具体数据块或条件。               |
|                      | **offset_end**          | 标记是否有偏移量结束，指示请求是否涉及数据范围的结束偏移。   |

## 对比分析

对比分析

| 分类                      | OCF 字段           | TSPRE 字段              | 作用对比与分析                                               |
| ------------------------- | ------------------ | ----------------------- | ------------------------------------------------------------ |
| **核心 IO 信息**          | ioi.io.addr        | obj_id                  | OCF：请求的起始地址，指定 IO 操作的起始位置。TSPRE：对象 ID，唯一标识对象 |
|                           | ioi.io.bytes       | obj_size                | OCF：请求的长度，定义数据范围。TSPRE：对象大小，记录存储空间需求。两者均描述数据量。 |
|                           | rw                 | op                      | OCF：读写方向（读/写）。TSPRE：操作类型（如 GET/SET/DELETE）。两者均定义操作类型，TSPRE 更通用。 |
|                           | data               | -                       | OCF：请求数据指针，指向数据缓冲区。TSPRE 无直接对应字段。    |
|                           | -                  | clock_time              | TSPRE：请求时间戳，记录请求发起时间。OCF 无直接对应字段，但 timestamp 类似。 |
|                           | -                  | hv                      | TSPRE：哈希值，用于快速定位或卸载到读取器。OCF 无类似字段。  |
|                           | -                  | valid                   | TSPRE：请求是否有效，过滤无效请求。OCF 无直接对应字段，但 error 可能相关。 |
| **缓存管理必要字段**      | cache              | -                       | OCF：缓存设备句柄，用于访问缓存系统。TSPRE 无直接对应字段。  |
|                           | core               | -                       | OCF：核心设备句柄，关联底层存储。TSPRE 无类似字段。          |
|                           | core_line_first    | -                       | OCF：缓存行映射的起始行。TSPRE 无类似字段。                  |
|                           | core_line_last     | -                       | OCF：缓存行映射的结束行。TSPRE 无类似字段。                  |
|                           | core_line_count    | -                       | OCF：缓存行数量。TSPRE 无类似字段。                          |
|                           | cache_mode         | -                       | OCF：缓存模式（如写回/写穿）。TSPRE 无直接对应字段。         |
|                           | part_id            | bucket_id               | OCF：分区 ID，标识数据分区。TSPRE：桶 ID，标识存储桶。两者功能类似，均用于分区管理。 |
|                           | dirty              | -                       | OCF：脏数据标记，指示未同步修改。TSPRE 无类似字段，但 overwrite 可能相关。 |
|                           | map                | -                       | OCF：缓存映射信息，记录缓存与存储映射。TSPRE 无类似字段。    |
|                           | -                  | ns                      | TSPRE：命名空间，区分数据集合。OCF 无类似字段，但 part_id 可能相关。 |
|                           | -                  | content_type            | TSPRE：内容类型，标识数据格式。OCF 无类似字段。              |
|                           | -                  | tenant_id               | TSPRE：租户 ID，支持多租户隔离。OCF 无类似字段。             |
| **请求状态和控制**        | ref_count          | -                       | OCF：引用计数，防止提前释放。TSPRE 无类似字段，但 n_req 可能相关。 |
|                           | req_remaining      | -                       | OCF：剩余 IO 操作数，记录未完成子操作。TSPRE 无类似字段。    |
|                           | error              | -                       | OCF：错误状态，记录 IO 错误。TSPRE 无直接对应字段，但 valid 可能相关。 |
|                           | complete           | -                       | OCF：完成回调，定义 IO 完成后的回调。TSPRE 无类似字段。      |
|                           | io_queue           | -                       | OCF：IO 队列句柄，管理请求调度。TSPRE 无类似字段。           |
|                           | -                  | n_req                   | TSPRE：请求计数，记录对象请求次数。OCF 无直接对应字段，但 ref_count 类似。 |
| **锁定和并发控制**        | lock_remaining     | -                       | OCF：待锁定缓存行数。TSPRE 无类似字段。                      |
|                           | alock_status       | -                       | OCF：锁状态映射，记录缓存行锁定状态。TSPRE 无类似字段。      |
|                           | alock_rw           | -                       | OCF：锁读写模式，指定锁类型。TSPRE 无类似字段。              |
|                           | lock_idx           | -                       | OCF：元数据锁索引，定位锁定的元数据。TSPRE 无类似字段。      |
| **缓存策略相关**          | force_pt           | -                       | OCF：强制直通，绕过缓存。TSPRE 无类似字段。                  |
|                           | part_evict         | -                       | OCF：分区驱逐标记，指示分区数据驱逐。TSPRE 无类似字段。      |
|                           | seq_cutoff         | -                       | OCF：顺序截断标记，优化顺序 IO。TSPRE 无类似字段。           |
|                           | -                  | ttl                     | TSPRE：生存时间，指定缓存生命周期。OCF 无直接对应字段。      |
|                           | -                  | next_access_vtime       | TSPRE：下次访问虚拟时间，预测访问模式。OCF 无类似字段。      |
|                           | -                  | eviction_algo_data      | TSPRE：驱逐算法数据，支持 LRU/LFU 等。OCF 无类似字段。       |
|                           | -                  | key_size/val_size       | TSPRE：键值大小，记录键值存储空间。OCF 无类似字段，但 byte_length 类似。 |
| **性能优化和跟踪**        | timestamp          | clock_time              | OCF：时间戳，记录请求时间。TSPRE：clock_time，功能相同。     |
|                           | sid                | -                       | OCF：序列 ID，唯一标识请求。TSPRE 无类似字段，但 obj_id 可能相关。 |
|                           | cp_data            | -                       | OCF：数据副本，用于优化场景。TSPRE 无类似字段。              |
|                           | -                  | vtime_since_last_access | TSPRE：自上次访问的虚拟时间，用于驱逐优化。OCF 无类似字段。  |
|                           | -                  | rtime_since_last_access | TSPRE：自上次访问的实际时间，用于性能分析。OCF 无类似字段。  |
|                           | -                  | prev_size               | TSPRE：之前大小，记录更新前大小。OCF 无类似字段。            |
|                           | -                  | create_rtime            | TSPRE：创建时间，记录对象首次缓存时间。OCF 无类似字段。      |
|                           | -                  | compulsory_miss         | TSPRE：强制缺失，标记缓存未命中原因。OCF 无类似字段。        |
|                           | -                  | overwrite               | TSPRE：是否覆盖对象，指示更新操作。OCF 无类似字段，但 dirty 可能相关。 |
|                           | -                  | first_seen_in_window    | TSPRE：在时间窗口内首次看到，标记首次访问。OCF 无类似字段。  |
| **内部实现细节/边缘字段** | ioi                | -                       | OCF：内部 IO 结构，存储底层 IO 细节。TSPRE 无类似字段。      |
|                           | engine_cbs         | -                       | OCF：引擎回调，定义缓存引擎回调。TSPRE 无类似字段。          |
|                           | io_if              | -                       | OCF：IO 接口，抽象 IO 操作层。TSPRE 无类似字段。             |
|                           | priv               | -                       | OCF：私有数据，存储特定实现信息。TSPRE 无类似字段。          |
|                           | master_io_req      | -                       | OCF：主 IO 请求，协调子请求。TSPRE 无类似字段。              |
|                           | master_io_req_type | -                       | OCF：主请求类型，标识主请求操作。TSPRE 无类似字段。          |
|                           | master_remaining   | -                       | OCF：主设备计数器，跟踪未完成 IO。TSPRE 无类似字段。         |
|                           | list               | -                       | OCF：链表节点，用于队列管理。TSPRE 无类似字段。              |
|                           | discard            | -                       | OCF：丢弃信息，记录需丢弃的数据。TSPRE 无类似字段。          |
|                           | -                  | age                     | TSPRE：年龄，记录缓存存留时间。OCF 无类似字段。              |
|                           | -                  | hostname                | TSPRE：主机名，标识请求来源主机。OCF 无类似字段。            |
|                           | -                  | extension               | TSPRE：扩展名，记录文件扩展名。OCF 无类似字段。              |
|                           | -                  | colo                    | TSPRE：托管位置，标识数据中心位置。OCF 无类似字段。          |
|                           | -                  | n_level/n_param         | TSPRE：级别和参数数量，存储分层配置。OCF 无类似字段。        |
|                           | -                  | method                  | TSPRE：方法，记录请求方法（如 HTTP 方法）。OCF 无类似字段。  |
|                           | -                  | prefetch_flag           | TSPRE：预取标志，触发数据预取。OCF 无类似字段。              |
|                           | -                  | trigger_block           | TSPRE：触发预取的块，记录预取条件。OCF 无类似字段。          |
|                           | -                  | offset_end              | TSPRE：偏移量结束标记，指示数据范围结束。OCF 无类似字段。    |



# ocf 缺少的信息

核心内容

1. cache->prefetcher->params

初始化预取器的参数，后续操作的时候需要提取预取器参数信息

包括 tsprefetchus 的参数以及其下两种子预取器的参数也要处理

2. req->trigger_block ， req->prefetch_flag 字段 和 req->offset_end 字段

是否为预取进入缓存，触发预取操作的对象

## 子专家

另外两种专家预取器执行操作的时候需要哪些内容，OCF 是否能够提供？

初始化 cache->prefetcher->params 的时候，同时初始化对应两种预取器的参数即可



