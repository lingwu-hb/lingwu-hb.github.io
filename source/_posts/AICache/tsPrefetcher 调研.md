---
title: tsPrefetcher 调研
date: 2025-06-29 12:55:08
categories:
  - data storage
tags:
  - 实习项目
---
有以下几个关键点：

1. 预取出来的 IO 会如何进行处理？会不会和原 IO 串行处理，从而影响原 IO？

空间上会抢占 cache 的空间；时间上，若生成预取 IO 的速度太慢，将会影响下一个原 IO 的处理速度。

2. 该预取器集成了时间和空间预取器？分别而言，时间和空间预取器各自是如何展开工作的呢？

详见下文 Mithril 和 OBL

# tsPrefetchus 预取器

## 概述

tsPrefetchus 是一个混合预取器，它结合了两种不同类型的预取策略：

1. **顺序预取器**（sequential prefetcher）：如 **OBL**, AMP, Leap 等
2. **历史预取器**（history prefetcher）：如 **Mithril**, PG 等

这个预取器的核心思想是动态调整这两种预取策略的权重，以适应不同的访问模式。

## 工作原理

### 混合预取策略

tsPrefetchus 同时使用顺序预取器和历史预取器来预测未来可能访问的对象：

- **顺序预取器**：基于空间局部性原理，预取与当前访问对象在空间上相邻的对象
- **历史预取器**：基于时间局部性和访问模式，预取历史上与当前访问模式相似的对象

### 自适应权重调整

tsPrefetchus 为每个预取器维护一个权重映射，根据预取效果动态调整权重：

- 当预取的对象被访问（命中）时，增加对应预取器的权重
- 当预取的对象被驱逐且未被访问时，减少对应预取器的权重

### 概率性预取决策

预取决策是概率性的，概率由各预取器的权重决定：

```
r = random(0, 1)
if (r < 预取器权重) {
    执行预取
}
```

这种机制允许系统在不同预取策略间进行探索和利用的平衡。

### 学习率动态调整

tsPrefetchus 使用动态学习率来控制权重调整的幅度：

- 定期计算当前命中率与先前命中率的变化
- 根据命中率变化和学习率变化的关系，调整学习率的方向和大小
- 当命中率持续降低或为零时，随机重置学习率以跳出局部最优

## 关键组件

### 预取执行

```
void tsPrefetchus_prefetch(cache_t *cache, const request_t *req) {
    // 获取预取器参数
    // 初始化权重（如果不存在）
    
    // 历史预取器部分
    r = random(0, 1)
    if (r < 历史预取器权重[req->obj_id]) {
        获取历史预取列表
        标记并插入预取对象
        更新统计信息
    }
    
    // 顺序预取器部分
    r = random(0, 1)
    if (r < 顺序预取器权重[merge_place]) {
        获取顺序预取列表
        标记并插入预取对象
        更新统计信息
    }
}
```

### 权重调整

参考论文 4.2.3 和 4.3.3 节部分内容

```
// 命中时增加权重
void tsPrefetchus_handle_find(cache_t *cache, const request_t *req, bool hit) {
    if (命中 && 是预取的对象) {
        if (顺序预取) {
            顺序预取器权重 *= exp(学习率)
        } else if (历史预取) {
            历史预取器权重 *= exp(学习率)
        }
        更新预取命中统计
    }
    
    // 定期更新学习率
    if (时间到达更新间隔) {
        更新学习率
    }
}

// 驱逐时减少权重
void tsPrefetchus_handle_evict(cache_t *cache, const request_t *check_req) {
    if (是预取的对象 && 未被访问) {
        if (顺序预取) {
            顺序预取器权重 *= exp(-学习率)
        } else if (历史预取) {
            历史预取器权重 *= exp(-学习率)
        }
    }
}
```

### 学习率调整

```
void ts_update_lr(cache_t *cache) {
    // 计算当前命中率
    hit_rate_current = num_hit / lr_update_interval
    
    // 计算变化
    delta_hit_rate = hit_rate_current - hit_rate_prev
    delta_lr = lr - lr_previous
    
    // 更新历史值
    lr_previous = lr
    hit_rate_prev = hit_rate_current
    
    // 调整学习率
    if (delta_lr != 0) {
        if (delta_hit_rate / delta_lr > 0) {
            增加学习率
        } else {
            减少学习率
        }
    } else {
        如果命中率为零或下降，增加unlearn_count
        如果unlearn_count达到阈值，随机重置学习率
    }
    
    // 重置命中计数
    num_hit = 0
}
```

## 工作流程总结

1. 调用 `tsPrefetchus_prefetch`，分别从历史预取器和顺序预取器获取预取候选列表
2. 根据各自权重决定是否执行预取
3. 预取的对象被标记来源（顺序或历史）
4. 当预取对象被访问或驱逐时，相应调整预取器权重
5. 定期更新学习率以优化预取效果

这种设计使 tsPrefetchus 能够适应不同的访问模式，在顺序访问和历史模式访问之间找到平衡，提高整体缓存命中率。

# Mithril

典型的时间关联预取策略

定期对偏移量请求时间矩阵进行时间关联关系的挖掘，具体而言，是如何执行定期挖掘的呢？

## 重要数据结构：

- 预取过程中用到

1. Mithril_params->prefetch_hashtable：哈希表，将对象ID映射到预取表数组中的索引位置，用于快速查找对象的预取候选项。每次挖掘的时候都需要更新该表。
2. Mithril_params->ptable_array：二维数组，内部组织格式为：

```
ptable_array[0]: [obj1, pf1, pf2, pf3, obj2, pf1, pf2, pf3, ...] (直到第1000个对象)
ptable_array[1]: [obj1001, pf1, pf2, pf3, obj1002, ...] (第1001到第2000个对象)
ptable_array[2]: [obj2001, pf1, pf2, pf3, ...] (第2001个对象开始)
```

- 记录和挖掘过程中用到：

3. 记录表：Mithril_params->rmtable->recording_table，一维数组
4. 挖掘表：Mithril_params->rmtable->mining_table，一维数组

## prefetch 流程

```
  // Lookup the current object in the prefetch hashtable to find its prefetch candidates
  gint prefetch_table_index =
      GPOINTER_TO_INT(g_hash_table_lookup(Mithril_params->prefetch_hashtable, GINT_TO_POINTER(req->obj_id)));

  // Calculate the position in the 2D prefetch table array
  // dim1: which shard in the array
  // dim2: position within the shard (each entry has pf_list_size+1 elements)
  gint dim1 = (gint)floor(prefetch_table_index / (double)PREFETCH_TABLE_SHARD_SIZE);
  gint dim2 = prefetch_table_index % PREFETCH_TABLE_SHARD_SIZE * (Mithril_params->pf_list_size + 1);

  // Iterate through prefetch candidates for this object
    // Start from 1 because index 0 stores the original object ID
    for (i = 1; i < Mithril_params->pf_list_size + 1; i++) {
      // If we reach the end of valid prefetch candidates, stop
      if (Mithril_params->ptable_array[dim1][dim2 + i] == 0) {
        break;
      }
      
      // Set the prefetch candidate's object ID and size
      new_req->obj_id = Mithril_params->ptable_array[dim1][dim2 + i];
      // Use block_size as the object size (previously used a size mapping)
      new_req->obj_size = Mithril_params->block_size;
    
      // Skip if the object is already in cache
      if (cache->find(cache, new_req, false)) {
        continue;
      }
    
      // Make room in the cache if needed by evicting objects
      while ((long)cache->get_occupied_byte(cache) + new_req->obj_size + cache->obj_md_size > (long)cache->cache_size) {
        cache->evict(cache, new_req);
      }

      // Insert the prefetched object into cache
      cache->insert(cache, new_req);
    }
```

## 挖掘流程

1. _Mithril_record_entry 流程

`find` 和 `evict` 的时候调用 `_Mithril_record_entry` 进行维护

用到了三个数据结构

记录表(recording table)：初始收集访问记录的表，存储对象ID和时间戳

挖掘表(mining table)：当记录达到一定条件后，从记录表移动到挖掘表进行模式分析

哈希表(hashtable)：用于快速查找对象在记录表或挖掘表中的位置

大致流程为：

**首先将请求放置到记录表中，出现一定次数之后转移到挖掘表中，若挖掘表长度满足阈值，调用**`**_Mithril_mining**`**函数进行挖掘操作**

2. _Mithril_mining 流程

假设我们有以下访问序列（对象ID和访问时间戳）：

- 挖掘表内容:

对象A: 时间戳 [10, 25, 40]

对象B: 时间戳 [11, 26, 41]

对象C: 时间戳 [20, 35, 50]

对象D: 时间戳 [30, 45, 60]

首先按照第一个时间戳进行排序

然后进行两两比较，A 和 B、C、D；B 和 C、D；C 和 D比较

- 比较A和B:

检查第一个时间戳差异: |10-11| = 1 < lookahead_range (假设为20)

时间戳数量相同，都是3个

比较时间戳序列相似性:

|10-11| = 1 (相邻，标记为关联)

|25-26| = 1 (相邻，关联确认)

|40-41| = 1 (相邻，关联确认)

associated_flag = TRUE，将A和B添加到预取表

- 比较A和C:

检查第一个时间戳差异: |10-20| = 10 < lookahead_range

时间戳数量相同，都是3个

比较时间戳序列相似性:

|10-20| = 10 (在范围内，但不相邻)

|25-35| = 10 (在范围内，但不相邻)

|40-50| = 10 (在范围内，但不相邻)

因为没有相邻时间戳，且first_flag已经为FALSE，所以associated_flag = FALSE，不添加到预取表

# OBL

典型的空间关联预取策略

## prefetch 流程

整体逻辑非常简单，直接预取下一个块的数据即可。

```
void OBL_prefetch(cache_t *cache, const request_t *req) {
    // 一个大的逻辑 io 会被划分为多个连续的块请求，一次逻辑 io 结束后才会进行预取
    if (req->offset_end && OBL_params->do_prefetch) {
        new_req->obj_size = OBL_params->block_size;
        new_req->obj_id = req->obj_id + 1;
        if (cache->find(cache, new_req, false)) {
            free_request(new_req);
            return;
        }
        // 如果 cache 空间不足，evict some space
        while (cache->get_occupied_byte(cache) + OBL_params->block_size + cache->obj_md_size > cache->cache_size) {
            cache->evict(cache, req);
        }
        if (strcasecmp(cache->prefetcher->name, "OBL") == 0) {
            cache->prefetcher->total_prefetch++;
            new_req->prefetch_flag = 1;
        }
        cache->insert(cache, new_req);
        free_request(new_req);
    }
}
```

`if (req->offset_end && OBL_params->do_prefetch)` 该判断逻辑中，req->offset_end 表示该 req 是否是一次逻辑 io 的最后一个 req。`OBL_params->do_prefetch` 由预取器进行维护。

```
typedef struct OBL_params {
  int32_t block_size;
  bool do_prefetch;

  uint32_t curr_idx;                // current index in the prev_access_block
  int32_t sequential_confidence_k;  // number of prev sequential accesses to be
                                    // considered as a sequential access
  obj_id_t* prev_access_block;      // prev k accessed
} OBL_params_t;
```

可以看到 `obj_id_t* prev_access_block` 中会保存 `int32_t sequential_confidence_k;` 个之前连续的访问，达到阈值之后，`do_prefetch` 参数才会被赋值为 `true`

# Das 中实现

## 问题

1. 同步和异步的问题

das 中预取推荐的过程和处理正常 IO 的过程是相互异步的，推荐的过程不会影响后续的正常 IO；

METS 中则是每次处理完成一个 IO 之后，都会进行预取操作

2. 多种专家更新需要一些信息

例如，更新权重需要知道传入的请求是否命中，传入到 das 中的请求，并不知道其是否命中。libCacheus 中并不存在多线程冲突问题，因为每个线程都有自己单独的 cache。但是 das 中需要考虑。  


## 流程

### 框架统一

1. 将目前的关联流改造成多专家模式中的其中一个专家（需要同步出一些接口函数）
2. 增加一个顺序流的专家（OBL）
3. 将两个专家嵌入成 tsprefetchus 接口，并设置权重更新机制

# tsPrefetcher 代码分析

1. 修改代码，先把结果输出出来
2. 梳理一下模拟器的运行环境和一些参数信息

## 参数信息

必要参数

trace_path：数据访问轨迹文件路径，支持zstd压缩格式

trace_type：轨迹文件类型，支持txt/csv/twr/vscsi/oracleGeneralBin等

eviction_algo：缓存替换算法，支持LRU/LFU/FIFO/ARC/LeCaR/Cacheus等

cache_size：缓存大小，支持字节单位或KB/MB/GB后缀

主要可选参数

轨迹读取相关

--trace-type-params/-t：CSV等轨迹的额外参数，如"obj-id-col=1;delimiter=,"

--num-req/-n：处理的请求数量，默认-1表示全部处理

--sample-ratio/-s：采样比例，1表示全采样，0.01表示采样1%的对象

--ignore-obj-size：忽略轨迹中的对象大小

缓存算法相关

--eviction-params/-e：替换算法的参数，如"n-seg=4"

--admission：准入算法，如size/bloom-filter/prob

--admission-params：准入算法参数

--prefetch：预取算法，如Mithril/OBL/PG/AMP/Prefetchus

--prefetch-params：预取算法参数，如"block-size=65536"

--consider-obj-metadata：是否考虑每个对象的元数据大小

其他选项

--output/-o：输出路径

--num-thread：多线程模式下的线程数，默认使用可用CPU核心数

--report-interval：单缓存运行时报告统计的频率

--warmup-sec：预热时间（秒）

--use-ttl：是否使用轨迹中的TTL信息

--verbose/-v：详细输出

模拟器内部处理流程

参数初始化和解析：通过parse_cmd函数解析命令行参数

轨迹读取器设置：根据指定的轨迹文件类型和参数配置读取器

缓存大小转换：将用户指定的缓存大小转换为字节单位，支持使用工作集大小的比例

缓存创建：为每个替换算法和缓存大小组合创建缓存实例

准入和预取配置：根据用户参数配置准入控制器和预取器

模拟执行：根据读取的轨迹数据运行缓存模拟

结果输出：输出模拟结果，包括命中率等性能指标

## 如何和 das 保持一致

需要注意的参数

1. 每级缓存容量
2. 缓存块大小
3. 写策略

4. ocf 中只有读请求，不考虑写，但是需要进行数据预埋

5. 淘汰策略
6. 访问延迟参数（用于模拟延迟时间）
7. 数据集

8. 这个可以直接下载部分数据集到本地，然后跑比较典型的 msrc 数据集

9. 高并发性（似乎无法模拟）

修改一些主要的配置参数，尝试保持和 das 一致。

1. 缓存大小
2. 测试集
3. 缓存策略

4. 周二才开始拿到完整项目，配置环境，成功跑起来
5. 还在对项目进行断点跟进调试

## 更换 trace 为 MSRC

tsPrefetcher 中主要由 reader 部件处理不同的 trace，reader 对外提供的核心接口为：read_one_req() 函数，用于提取一个正确的请求。





