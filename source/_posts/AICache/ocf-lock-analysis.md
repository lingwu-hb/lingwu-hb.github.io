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

## 快速和慢速获取缓存行锁

需要注意以下两个变量的联系

* `req->alock_status`：uint8 类型，其数位保存当前请求需要的缓存行的锁状态。
* `req->cache->device.concurrency->cache_line->access`：原子类型变量，用于监控系统中所有缓存行锁的状态。

`req->cache->device->concurrency.cache_line` 就是 ocf_alock 类型的变量。后续的 alock 就是指代该全局变量

在 OCF (Open CAS Framework) 中，缓存行锁定机制涉及两个关键字段：`alock->access` 和 `req->alock_status`。这两个字段虽然都与缓存行锁定有关，但它们在系统中扮演着不同的角色。

### alock->access 字段

#### 定义与结构

`alock->access` 是一个原子变量数组，每个缓存行对应一个原子变量，用于表示缓存行的实际锁定状态。

```c
struct ocf_alock {
  env_atomic *access; *// 每个缓存行的锁状态*
  *// 其他字段...*
};
```

#### 功能

全局锁状态管理：记录**系统**中每个缓存行的实际锁定状态

原子操作：通过原子操作确保并发安全

锁状态值：

* `OCF_CACHE_LINE_ACCESS_IDLE (0)`：缓存行空闲

* `OCF_CACHE_LINE_ACCESS_ONE_RD (1)`：一个读锁

* \`>1`：多个读锁

* `OCF_CACHE_LINE_ACCESS_WR (INT_MAX)`：写锁

#### 使用方式

如在 `ocf_alock_trylock_entry_rd_idle` 函数中：

```c
env_atomic *access = &alock->access[entry];
int prev = env_atomic_cmpxchg(access, OCF_CACHE_LINE_ACCESS_IDLE, OCF_CACHE_LINE_ACCESS_ONE_RD);
```

这里使用原子比较交换操作尝试将缓存行从空闲状态更改为一个读锁状态。

### req->alock_status 字段

#### 定义与结构

`req->alock_status` 是一个请求特定的字段，是一个指向 uint8_t 数组的指针，用于跟踪**请求**中每个缓存行的锁定状态。

```c
struct ocf_request {
  *// 其他字段...*
  uint8_t* alock_status; *// 请求中每个缓存行的锁定状态*
  *// 其他字段...*
};
```

#### 功能

1. **请求级别跟踪**：记录特定请求中哪些缓存行已被锁定

2. 锁定标记：通常是简单的布尔值（0表示未锁定，非0表示已锁定），**无法知道锁的类型**

3. 请求完成时解锁：帮助在请求完成时知道哪些缓存行需要解锁

#### 使用方式

通过 `ocf_alock_mark_index_locked` 函数设置：

```c
void ocf_alock_mark_index_locked(struct ocf_alock *alock,
		struct ocf_request *req, unsigned index, bool locked)
{ // locked == true: 进行锁定; locked == false: 进行解锁
	if (locked) 
		env_bit_set(index, req->alock_status);
	else
		env_bit_clear(index, req->alock_status);
}
```

### 两者的区别

作用域不同：

`alock->access`：全局作用域，表示缓存系统中每个缓存行的实际锁状态

`req->alock_status`：请求作用域，仅跟踪特定请求中缓存行的锁定状态

数据类型不同：

`alock->access`：原子变量数组，支持复杂的原子操作

`req->alock_status`：简单的 uint8_t 数组，通常只存储布尔值

用途不同：

`alock->access`：实际执行锁定/解锁操作

`req->alock_status`：跟踪请求中哪些缓存行已被锁定，便于请求完成时解锁

### 两者的联系

协同工作：

当请求尝试锁定缓存行时，首先通过 `alock->access` 获取实际锁

锁定成功后，通过 `req->alock_status` 标记该请求已锁定此缓存行

锁定/解锁流程：

锁定流程：

1. 尝试通过 `alock->access` 获取锁

2. 成功后，设置 `req->alock_status` 中对应数位为 1

解锁流程：

1. 遍历 `req->alock_status` 找出已锁定的缓存行

2. 通过 `alock->access` 解锁这些缓存行

3. 设置 `req->alock_status` 中对应数位为 0

请求完成时的解锁：

```c
void ocf_req_unlock(struct ocf_alock *c, struct ocf_request *req) {
    // 根据 req->alock_rw 和 req->alock_status 决定如何解锁
    if (req->alock_rw == OCF_READ)
      ocf_req_unlock_rd(c, req);
    else if (req->alock_rw == OCF_WRITE)
      ocf_req_unlock_wr(c, req);
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

