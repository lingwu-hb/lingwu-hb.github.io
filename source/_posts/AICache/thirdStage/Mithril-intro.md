---
title: Mithril intro
date: 2025-07-09 16:40:28
categories:
- data storage
tags:
- prefetch algo
---

# Mithril 算法数据结构

## rec_mining_t 数据结构

`rec_mining_t` 是 Mithril 算法中用于记录和挖掘访问模式的核心数据结构，它包含以下关键组件：

### 主要组件

| 组件 | 类型 | 描述 |
|------|------|------|
| `hashtable` | `GHashTable*` | 哈希表，存储块相关信息。键为块号，值为行号（指向记录表或挖掘表）。<br>- 正值：指向记录表<br>- 负值：指向挖掘表 |
| `recording_table` | `gint64*` | 记录表，结构为 N*(min_support/4+1) 数组。<br>- 其中 4 是一个 64 位整数中存储的时间戳数量<br>- N 是记录表中的条目数<br>- 加 1 是为了标签 |
| `rtable_row_len` | `gint8` | 记录表的行长度，当前为 min_support/4 + 1 |
| `n_rows_in_rtable` | `gint64` | 记录表中的行数，决定记录表可以存储多少块 |
| `rtable_cur_row` | `gint64` | 记录表中的当前行号 |
| `mtable_row_len` | `gint8` | 挖掘表的行长度，当前为 max_support/4 + 1 |
| `mining_table` | `GArray*` | 挖掘表位置，使用 GArray 以便快速追加 |
| `n_avail_mining` | `gint` | 计数器，表示挖掘表中有多少对象/块已准备好进行挖掘 |

### 设计理念

记录表（recording table）和挖掘表（mining table）是两种不同阶段的数据结构：

1. **记录表**：初始阶段收集块访问信息
   - 当块被访问次数不足以成为频繁块时，其信息存储在记录表中
   - 如果块在记录表中停留太久，说明它是罕见的，没有积累足够的访问次数迁移到挖掘表
   - 因此，为记录表分配过多空间并不实用

2. **挖掘表**：存储频繁访问的块，用于模式挖掘
   - 当块的访问次数达到 min_support 阈值时，从记录表迁移到挖掘表
   - 挖掘表中的数据用于识别关联访问模式

### 时间戳存储机制

时间戳在 64 位整数中按以下格式存储：
- 前 4 位：时间戳数量（0~4）
- 每 15 位：一个时间戳
  - 第一个时间戳存储在 4-18 位
  - 第二个时间戳存储在 19-33 位
  - 第三个时间戳存储在 34-48 位
  - 第四个时间戳存储在 49-63 位

## 记录表（recording_table）结构详解

记录表是 Mithril 算法中用于初始收集访问模式的关键数据结构。它的内存结构为 `N*(min_support/4+1)` 的二维数组，其中：

### 内存分配与布局

```c
// 在 set_Mithril_params 函数中初始化记录表
rmtable->n_rows_in_rtable = (gint64)(cache_size * RECORDING_TABLE_MAXIMAL /
                         ((int)ceil((double)Mithril_params->min_support / (double)2) * 2 + 8 + 4));
if (rmtable->n_rows_in_rtable < 1000) {
  rmtable->n_rows_in_rtable = 1000;
}
rmtable->rtable_row_len = (gint)ceil((double)Mithril_params->min_support / (double)4) + 1;
rmtable->recording_table = g_new0(gint64, rmtable->n_rows_in_rtable * rmtable->rtable_row_len);
```

1. **行数（N）计算**：
   - 根据缓存大小乘以 `RECORDING_TABLE_MAXIMAL`（默认值为 0.02，即缓存大小的 2%）
   - 除以每行所需的字节数来确定可以存储的行数
   - 最小行数为 1000，确保小缓存也有足够的记录空间

2. **行长度计算**：
   - `rtable_row_len = ceil(min_support/4) + 1`
   - 其中 4 表示每个 64 位整数可以存储的时间戳数量
   - 加 1 是为第一个元素预留空间，用于存储块ID（obj_id）

### 记录表行结构

每行在记录表中的布局如下：

```
| 位置[0]  | 位置[1]        | 位置[2]        | ... | 位置[rtable_row_len-1] |
| 块ID     | 时间戳组(0-4个) | 时间戳组(0-4个) | ... | 时间戳组(0-4个)        |
```

- **位置[0]**：存储块ID（obj_id），用于标识这一行记录的是哪个块
- **位置[1]到位置[rtable_row_len-1]**：每个位置存储一个 64 位整数，每个整数最多可以存储 4 个时间戳

### 时间戳添加机制

当一个块被访问时，Mithril 会在记录表中添加一个时间戳：

```c
// 在 _Mithril_record_entry 函数中
for (i = 1; i < rmtable->rtable_row_len; i++) {
  timestamps_length += NUM_OF_TS(row_in_rtable[i]);
  if (NUM_OF_TS(row_in_rtable[i]) < 4) {
    row_in_rtable[i] = ADD_TS(row_in_rtable[i], Mithril_params->ts);
    break;
  }
}
```

1. 扫描行中的每个 64 位整数，查找还没存满 4 个时间戳的整数
2. 使用 `ADD_TS` 宏添加当前时间戳到这个整数中
3. 如果一行中的时间戳总数达到 `min_support`，说明这个块已经足够频繁，会被迁移到挖掘表

### 记录表填充示例

假设 `min_support = 10`，则 `rtable_row_len = ceil(10/4) + 1 = 4`：

```
| 位置[0]  | 位置[1]    | 位置[2]    | 位置[3]    |
| 块ID=123 | 4个时间戳  | 4个时间戳  | 2个时间戳  |
```

这一行表示块ID为123的块已经被访问了10次，其中：
- 位置[1]存储了前4次访问的时间戳
- 位置[2]存储了接下来4次访问的时间戳
- 位置[3]存储了最后2次访问的时间戳

当时间戳数量达到 `min_support` 时，这个块会从记录表迁移到挖掘表，用于进一步的模式挖掘。

# Mithril 流程

## 保存到记录表

```c
  // Mithril.c Line 302 - Line 308
  // 1. record entry when rec_trigger is each_req.
  // 2. record entry when (rec_trigger is miss or miss_evict (in other words,
  // !evict)) && !hit
  if ((Mithril_params->rec_trigger == each_req) ||
      (Mithril_params->rec_trigger != evict && !hit)) {
    _Mithril_record_entry(cache, req);
  }
```

`Mithril_params->rec_trigger` 枚举类型，决定了什么时候记录 IO。共有四种类型：miss/evict/miss_evict/each_req

## 记录表到挖掘表

Mithril 在块的访问次数（时间戳数量）达到 `min_support` 时，会将块从记录表迁移到挖掘表：

```c
// Mithril.c 第 976-985 行
if (timestamps_length == Mithril_params->min_support - 1) {
  /* time to move to mining table */
  // gint64 *array_ele = malloc(sizeof(gint64) *
  // rmtable->mtable_row_len);
  gint64 array_ele[rmtable->mtable_row_len];
  memcpy(array_ele, row_in_rtable,
         sizeof(TS_REPRESENTATION) * rmtable->rtable_row_len);

  // ... 将行从记录表拷贝到挖掘表 ...
}
```

这一过程的关键步骤包括：

1. **检测访问频率阈值**：当一个块在记录表中的时间戳数量达到 `min_support - 1` 时，下一次访问会触发迁移
2. **数据复制与扩展**：从记录表复制现有数据到挖掘表，并为可能的额外时间戳预留空间
3. **哈希表索引更新**：更新哈希表中块ID到表位置的映射，使用负值标记其在挖掘表中的位置
4. **空间回收**：清空记录表中迁移出的条目，以便重用空间

当挖掘表中的条目数量达到阈值时，会触发挖掘过程：

```c
// Mithril.c 第 1068-1072 行
if (rmtable->n_avail_mining >= Mithril_params->mtable_size ||
    (Mithril_params->min_support == 1 &&
     rmtable->n_avail_mining > Mithril_params->mining_threshold / 8)) {
  _Mithril_mining(cache);
  rmtable->n_avail_mining = 0;
}
```

## 挖掘表到预取表

挖掘表积累足够条目后，Mithril 会执行模式挖掘，寻找块之间的访问关联：

```c
// Mithril.c 第 1156-1208 行
for (i = 0; i < (long)rmtable->mining_table->len - 1; i++) {
  item1 = GET_ROW_IN_MTABLE(Mithril_params, i);
  num_of_ts1 = _Mithril_get_total_num_of_ts(item1, rmtable->mtable_row_len);
  first_flag = TRUE;

  for (j = i + 1; j < (long)rmtable->mining_table->len; j++) {
    item2 = GET_ROW_IN_MTABLE(Mithril_params, j);

    // 如果第一个时间戳差距过大，就跳过
    if (GET_NTH_TS(item2, 1) - GET_NTH_TS(item1, 1) >
        Mithril_params->lookahead_range) {
      break;
    }
    
    // ... 分析时间戳是否符合关联条件 ...

    if (associated_flag) {
      // 将关联的块添加到预取表
      _Mithril_add_to_prefetch_table(cache, GINT_TO_POINTER(item1[0]),
                                   GINT_TO_POINTER(item2[0]));
    }
  }
}
```

挖掘的核心步骤：

1. **排序和比对**：先按时间戳排序挖掘表，然后依次比较不同块的访问模式
2. **时间相关性判断**：计算时间戳之间的差距，如果在 `lookahead_range` 范围内，可能存在关联
3. **置信度检查**：通过对比多个时间戳，确认关联不是偶然的，错误次数不超过 `confidence` 阈值
4. **构建预取关系**：将发现的关联添加到预取表中，作为未来预取决策的依据

预取表的构建机制确保了：

```c
// Mithril.c 第 1301-1324 行
// 构建预取表项
Mithril_params->ptable_array[dim1][dim2 + 1] = GPOINTER_TO_INT(gp2);
Mithril_params->ptable_array[dim1][dim2] = GPOINTER_TO_INT(gp1);

// 更新哈希表索引
g_hash_table_insert(Mithril_params->prefetch_hashtable, gp1,
                    GINT_TO_POINTER(Mithril_params->ptable_cur_row));
```

当缓存接收到一个请求时，Mithril 会查找预取表进行预取：

```c
// Mithril.c 第 390-405 行
gint prefetch_table_index = GPOINTER_TO_INT(g_hash_table_lookup(
    Mithril_params->prefetch_hashtable, GINT_TO_POINTER(req->obj_id)));

// ... 获取预取表中的预取项 ...

if (prefetch_table_index) {
  // 从预取表获取关联块并进行预取
  for (i = 1; i < Mithril_params->pf_list_size + 1; i++) {
    if (Mithril_params->ptable_array[dim1][dim2 + i] == 0) {
      break;
    }
    new_req->obj_id = Mithril_params->ptable_array[dim1][dim2 + i];
    
    // ... 执行实际预取操作 ...
  }
}
```

## 流程图示

![Mithril示意图](\img\Mithril示意图.png)

最上面是简化的记录表

左侧是挖掘表

最右侧是判断两个请求是否相关联。如果相关联，将其存入到预取表（哈希表）。预取表中，key -> 触发预取的请求，value -> 与 key 相关联的请求。



### 为什么过滤超高频块？

> 此部分为补充内容

在 Mithril 算法中，当一个块在挖掘表中的访问次数超过 `max_support` 时，该块会被从挖掘表中删除。这种设计看似违反直觉（因为高频访问的块理应更重要），但实际上有深思熟虑的考量：

1. 过滤噪音和普遍模式

- **识别无信息价值的常见块**：访问极其频繁的块通常是系统文件、元数据或程序必备组件
- **降低关联分析的干扰**：这些块几乎在任何情况下都会被访问，与其他块的关联性不具特殊意义
- **提高模式质量**：类似文本分析中过滤掉"the"、"a"等常见词，删除"太常见"的块可降低挖掘中的噪音

2. 提高关联模式的价值

- **聚焦有价值的模式**：Mithril 的核心目标是发现有预测价值的访问模式关联
- **中频块的优势**：介于 `min_support` 和 `max_support` 之间的中等频率块往往形成更有意义的模式
- **避免低质量关联**：超高频块与太多其他块都有关联，这些关联通常不够特异，预测价值有限

3. 资源和性能优化

- **内存效率**：保留和处理超高频块会占用宝贵的内存和计算资源
- **聚焦关键区间**：将资源集中于频率适中的块，可提高整体预测效率
- **降低计算复杂度**：挖掘算法的复杂度通常与考虑的项目数量相关，删除超高频项可显著减轻计算负担

4. 数据挖掘中的精准平衡

这种设计体现了数据挖掘中的一个关键原则：**并非所有频繁出现的模式都有价值**。通过设置 `min_support` 和 `max_support` 两个阈值，Mithril 算法可以专注于"恰到好处"的频率区间，提高预测的质量和效率。这是频繁模式挖掘算法中常见的优化技术，平衡了覆盖率和精确度。


## 重要参数

Mithril 算法的关键参数及其影响：

| 参数 | 默认值 | 描述 |
|------|------|------|
| `min_support` | 2 | 最小支持度，决定一个块多少次访问后从记录表迁移到挖掘表 |
| `max_support` | 8 | 最大支持度，超过此值的块会被从挖掘表中删除，避免过度频繁的块干扰模式挖掘 |
| `lookahead_range` | 20 | 时间戳比较范围，决定多大时间差内的访问被视为关联 |
| `confidence` | 1 | 置信度，表示可接受的时间戳不匹配次数，影响关联发现的容错性 |
| `pf_list_size` | 2 | 每个块关联的预取对象最大数量，影响预取广度 |
| `rec_trigger` | each_req | 记录触发器，决定何时记录块访问（miss/evict/miss_evict/each_req） |
| `mining_threshold` | 5120 | 挖掘阈值，决定挖掘表达到多少条目时触发挖掘过程 |
| `sequential_type` | 0 | 顺序预取类型，是否启用简单的顺序预取策略 |

这些参数共同影响 Mithril 的预取性能与资源消耗，可以根据不同的工作负载特性进行调整，以优化命中率和资源利用。例如：

- 频繁变化的工作负载可能需要较小的 `lookahead_range`
- 访问模式明显的工作负载可以使用较大的 `confidence` 提高容错性
- 资源受限环境可以降低 `pf_list_size` 减少预取开销
