---
title: hash algorithm
date: 2024-05-23 09:45:02
categories:
- data storage
tags:
- similarity hash
- Consistent Hash
---



## 一致性哈希

主要用于解决系统中负载均衡的问题，Nginx中应用此方案。

[参考文章](https://www.xiaolincoding.com/os/8_network_system/hash.html#%E5%A6%82%E4%BD%95%E5%88%86%E9%85%8D%E8%AF%B7%E6%B1%82)



## 相似性搜索（局部敏感哈希算法）

### 要解决的问题

如何在海量的信息中，检索到相似度比较高的信息

### 基本思想

1. 利用shingle对文本收集k-gram，形成one-hot encoding的序列
2. 利用minhash算法，将稀疏的向量转变为稠密的向量
3. 利用LSH（locality sensitive hashing）算法，对向量分块进行映射，部分块产生映射冲突的向量视为候选向量，再计算其相似度。

[参考文章](https://zhuanlan.zhihu.com/p/678735907)
