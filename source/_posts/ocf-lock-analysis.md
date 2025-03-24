---
title: ocf lock analysis
date: 2025-03-24 11:28:05
categories:
- data storage
tags:
- ocf
- lock
---

# 锁机制分析

OCF 中设计了多种多样的锁来进行并发控制。最常见的为元数据锁和缓存行锁。

## 元数据锁

缓存相关的元数据，包括缓存映射信息、缓存哈希表数据以及缓存状态信息等。

```c
// 获取元数据的读锁，后续读取元数据信息
ocf_hb_req_prot_lock_rd(req);
ocf_hb_req_prot_unlock_rd(req);
// 锁升级，先释放掉所有的读锁，然后再拿去写锁。顺序拿取，防止死锁
ocf_hb_req_prot_lock_upgrade(req);
ocf_hb_req_prot_unlock_wr(req);
```

## 缓存行锁

缓存行锁针对的粒度为**缓存行**，并且使用了分级获取的方式

首先尝试快速获取锁，如果快速获取锁失败，再慢速获取锁。

快速获取是同步进行获取，不会阻塞，一旦有一个缓存行获取失败，直接退出。

慢速获取会尝试获取每一个锁，如果获取不到，将会考虑将其放置到等待队列，直到成功获取锁才执行回调函数。（代码片段如下）

```c
int ocf_alock_lock_rd(struct ocf_alock *alock,
		struct ocf_request *req, ocf_req_async_lock_cb cmpl)
{
	// 尝试快速获取锁
	lock = alock->cbs->lock_entries_fast(alock, req, OCF_READ);
	if (lock != OCF_LOCK_ACQUIRED) {
		// 快速获取失败，执行慢速获取
		status = alock->cbs->lock_entries_slow(alock, req, OCF_READ, cmpl);
	}
	return lock;
}
```



## 锁 tradeoff

在尝试实现历史哈希表 v3.0 的时候，给历史哈希表加了粗粒度的锁。

结果发现系统接近 40% 的耗时发生在历史哈希表相关函数中，极大的影响了性能。

思考之后发现，对于历史哈希表这类影响不大的构件，放弃一致性，往往是更好的选择。

（TODO：思索什么时候应该加锁，什么时候又不应该加锁呢？如果要加锁，怎么加锁才能最大限度得降低对性能的影响呢？并发编程需要考虑这些）



## 细粒度锁机制

> 问题：ocf_core_submit_io_fast 流程执行完，已经知道缓存中不存在当前请求的元素，为什么在后续的 read_generic 流程中还需要对缓存进行加锁判断缓存中是否映射请求的数据呢？

这就是需要考虑 OCF 中的细粒度锁机制了。由于 fio 是 128 粒度并发下发 IO 的，因此当前请求在执行 fast 读 cache 未命中后，到 read_generic 之前这段时间内，OCF 并没有对缓存加任何锁，其他进程可能在这段时间内对缓存元数据和缓存进行修改。因此，执行到 read_generic 处还需要再对缓存上锁进行判断。

这里需要再上锁分析的根本原因就是 OCF 没有给缓存上粗粒度的锁，为了性能产生了一些前后不一致性的存在。所以后续需要再上锁进行弥补可能产生的不一致性。本质上也是出于 tradeoff 的考虑。

