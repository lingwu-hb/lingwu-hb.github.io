---
title: RL paper survey
date: 2025-07-04 10:03:02
categories:
- [paper]
- [data storage]
tags:
- algorithm
- RL
- 实习项目
---



# 1. ArtMem

ArtMem：Adaptive Migration in Reinforcement Learning-Enabled Tiered Memory

## 背景：

内存系统只靠 DRAM 不足，因此引入 PM 和基于 CXL 的额外内存，形成快慢速的分层内存系统。

但现有分层内存系统中的页面迁移策略不够 adaptive，没有充分考虑到工作负载的动态性，因此引入强化学习策略。

## 核心技术

1. 通过 EMA 反应一个页面的最近访问频率高
2. 通过 **RL** 动态调整热页面阈值参数，如果一个页面的 EMA 值超过热页面阈值，该页面将被迁移到快速内存。



## 关联文章

1. CHROME: Concurrency-Aware Holistic Cache Management Framework with Online Reinforcement Learning

利用强化学习对缓存行为做决策。
