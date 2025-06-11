---
title: About cache prefetcher
date: 2024-10-22 15:19:39
categories:
- [paper]
- [data storage]
tags:
- cache prefetcher
---

> 这篇文章主要记录调研的cache prefetch部分有价值的论文，并给出一些总结

# Baleen

### 核心内容

1. ML learning-based admission policy + prefetch.
2. exploit a new cache residency model to guide model training.

首先对 access pattern 进行了统计分析，提取出了一种缓存驻留模型（episodes），如果一批访问对应于一个缓存驻留模型，就将其进行分组。使用该模型对数据进行整理分析，并使用其训练ML准入模型。

重点就是 **episodes 缓存驻留模型**。episodes 模型将一组对同一个块的访问进行聚集处理，一个块基本上对应于 HDD 的一个盘块，多个对同一个盘块的访问同时读取，会极大得降低对 HDD 的带宽压力，这也正是 HW 项目所需要和重视的。



### 相关背景部分介绍

该篇文章针对 Tectonic 数据库的 trace 进行设计，考虑单个存储节点的性能。

本篇论文中提到的准入策略还是为了权衡 flash cache 对 HDD 的性能提升作用和 flash cache 本身的磨损开销。而 HW 项目中涉及到的准入算法主要还是针对 HDD 的盘带宽进行设计，并不侧重 SDD 的容量和磨碎开销。

现存的缓存系统存在的部分问题

1. 非模块化
2. 没有聚焦系统端到端指标
3. 没有考虑峰值负载
4. 没有进行组件协同（准入、预取和淘汰）

本文提出的解决方案

1. 定义 DT（Disk-head time） + 阐述 **DT 作为评价指标的全面性**
2. 定义了 TCO，确定了降低 peak TD 和 HDDs 是降低 TCO 的关键
3. 预取的单位为 segments，首先判断哪些 segment 需要预取，然后再判断什么时候预取（衡量预取带来的收益和错误预测的代价）
4. **详细阐述了 episodes，如何进行分组，如何设定参数，以及使用 episodes 的好处。（论文$3.4）**
5. 描述 OPT（an episode-based approximation of optimal admission）的原理，以及如何利用 OPT 来进行预取处理

这种预取相当于识别了一种访存模式，一个 episodes 对应于一种访存模式，当下次在遇到此类访存模式时，系统就知道如何进行预取后续的 segments 到 flash cache 中。

### Baleen 具体实现方案

总共使用了9个特征信息，包括离线的元数据信息和在线的访问情况

使用GBM来做二分类问题，作为准入策略。

![Baleen架构图](https://s2.loli.net/2024/10/22/O4TBP7CzHNbjwuG.jpg)

​                                                                              Fig6：Architecture

1. 访问记录被分为若干 Episodes，然后送入到 Admission Policy 中进行训练，从而训练出一个二分类模型。
2. 在开发和测试过程中，使用离线训练+在线模拟器调节的方式对模型进行收敛

Q：

1. HDD 按照块（block）为单位进行划分，上层每次读取都会读取一块？但是 Baleen 不按照块级进行缓存，而是按照 episodes 进行分组，按照 segments 为单位进行处理？

在每一次读取的时候，缓存会检查该次访问所需要的 segments 是否全部被缓存了，如果还有段缺失，则需要被读入到缓存中。

2. $3.5中的 block、access、episodes 之间的关系？

一个 episodes 由多个 access 组成，只针对于一个 block。

补充内容

1. 布隆过滤器

布隆过滤器就是一串二进制01数组A（初始化全零） + 若干个哈希函数 Funcx。当一个 key “存入”布隆过滤器时，A[Funcx(key)] = 1。后续查询该 key 是否存在时，检查每个 A[Funcx(key)] 是否为1。

布隆过滤器的优点在于可以高效判断一个数据是否存在于系统中，缺点在于存在误判率，没法达到百分之百的准确率。

布隆过滤器常用于防止 redis 缓存穿透。如果大量请求跳过 redis 缓存，直接查询了数据库，会对数据库造成很大的压力，叫做 redis 缓存穿透。布隆过滤器的二进制数据是全局的，若数据库中存在数据，那么布隆过滤器就会在该数据请求过后标记数据的存在。从而避免其他大量数据库不存在的数据请求，造成 redis 缓存穿透。

## Baleen 代码部分解析

跟踪调试

主程序调用 simulate_cache_driver(options)，其中 options 为该系统执行所需要的全部配置信息。

1. 配置日志信息
2. 明确替换策略为 LRU
3. 计算 num_cache_elems，缓存元素的数量
4. 构建 ap，如果使用离线 ap，则直接加载；否则需要进行在线构建（Line1482跳转）
5. 构建 prefetcher（Line1488跳转）
6. 确定 eviction 策略
7. 模拟缓存系统，然后开始模拟执行访问请求（Line1560）

整体 demo 代码分为两步：

1. 利用 trace 对 ML 模型进行训练
2. 将训练好的 Baleen 和模拟器进行在线测试

Q1：模拟器主要模拟真实系统中的哪些部分？

Baleen 系统跑到模拟器上，没有涉及到真实的硬件。

Q2：ML 准入和预取模型结构是什么样子的？

都是 LightGBN 的模型结构，分为分类模型和回归模型两种。

Q3：代码中是如何对 Trace 进行处理，从而得到 episodes 的？

episodes.py 中的 Line875 位置即为将 Trace 数据转换为 episodes 的地方

```Python
def process_obj_chunk_n_noprefetch(obj):
    d_ = interarrivals_from_accesses(obj)
    residences_by_e_age = {}
    for e_age_log_phy in obj['e_ages']:
        e_age_split = e_age_log_phy[d_['split_idx']]
        residencies = []
        for first, last, no_of_accesses in residences_from_interarrivals(d_['interarrivals'], e_age_split):
            chunk_counts, chunk_last_seen = get_chunk_stats(first, last, d_)
            episode_ = get_episode(d_, first, last, no_of_accesses, chunk_counts=chunk_counts, chunk_last_seen=chunk_last_seen)
            update_noprefetch_stats(first, last, d_, episode_, no_of_accesses, e_age_split)
            residencies.append(episode_)
        residences_by_e_age[e_age_log_phy] = residencies
    return residences_by_e_age
```

Q4：定位到离线训练和在线训练的位置，各自的作用

根据需求进行选择。可以在conf文件中定义对应字段的值，决定是否需要在线训练。

在构建AP的时候，选择合适的参数即可

# CHROME

## 核心内容

利用强化学习中的 `Q-learing` 算法框架对存储管理系统进行集成管理。整体上算是一种最简单的 `Q-learning` 算法的应用，硬件开销相对较小。CHROME 在 CPU 的 LLC（last level cache）和 L2 级缓存中进行缓存管理。

## 算法框架

CHROME 在强化学习中的各大基本概念定义：

* agent：CHROME

* env：CPU 和内存

* state：以多维向量形式表示的程序特征信息（包括 PC 等程序信息和 page number, page offset 等数据访问信息）

> 注：为了权衡资源开销和性能，利用 feature selection[27] 来决定选择哪些特征进行处理

* action：bypass or assign EPV(eviction priority value) on a cache miss; update EPV on a cache hit

* reward：分为四种奖励

![CHROME总体架构图](https://s2.loli.net/2024/10/22/BX1DEWMAQN84z3k.png)

​																						CHROME架构图

表中内容细节

EQ：Each EQ entry records five pieces of information: the state vector, the action executed by CHROME, whether the action was triggered by a hit or a miss, the memory address of the requested cache block, and the assigned reward.

Q2：什么时候给 EQ 中的项赋 award 值呢？是在下一个请求到来的时候吗？

For each new LLC request, if the request address matches the address stored in an EQ entry (indicating that CHROME has previously executed an action for this address and this address is now being requested again within a temporal window

This reward is determined based on whether the corresponding action results in a cache hit or a miss, and whether the LLC request is triggered by demand or prefetch

![CHROME伪代码](https://s2.loli.net/2024/10/22/Jo3wC4pKjkzNXWi.png)

​																							CHROME伪代码

# 总结

|          |                            Baleen                            |                        CHROME                        |
| :------: | :----------------------------------------------------------: | :--------------------------------------------------: |
| 工作层次 |                          SSD - HDD                           |                     CPU 三级缓存                     |
| 所用算法 |                机器学习中常见的分类和回归算法                |             强化学习中的 Q-learning 算法             |
|   优点   | 1. episodes 缓存驻留模型能够降低 HDD 带宽压力<br />2. 考虑了极限负载（peak load）的情况，更符合真实的应用场景 | 利用强化学习将缓存替换，准入和预取集成到同一个系统中 |



# 参考文章

> [1] FAST'24 Baleen: ML Admission & Prefetching for Flash Caches
>
> [2] HPCA'24 CHROME: Concurrency-Aware Holistic Cache Management Framework with Online Reinforcement Learning
