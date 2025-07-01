---
title: spdk
date: 2025-07-01 09:55:48
categories:
- data storage
tags:
- spdk
- ocf
---







# 文档

本文档主要用于梳理 spdk 相关概念和代码



简单理解就是：

spdk 让应用程序可以直接访问到底层的存储介质，避免了繁琐的中断操作，从而提升了存储效率（不太确定）

ocf 作为缓存管理框架，用于管理多级缓存的存储工作，能够封装底层的多级缓存，提供更加快速的缓存读写操作和多种读写策略。





> :exclamation: 以下内容由 cursor 生成，仅供参考 :exclamation:

## spdk 与 ocf 之间的桥梁

module/bdev/ocf 文件夹是连接 SPDK 和 OCF 的桥梁，它实现了一个 SPDK 块设备（bdev）模块，让 OCF 缓存功能能够在 SPDK 框架中使用。

## 主要文件及其功能

1. vbdev_ocf.c/h：

- 实现了虚拟块设备（Virtual Block Device）的核心功能

- 定义了 OCF 缓存设备在 SPDK 中的表示和行为

- 处理设备的注册、初始化和销毁

- 管理 I/O 操作的提交和完成

1. vbdev_ocf_rpc.c：

- 实现了 RPC（远程过程调用）接口

- 允许用户通过 SPDK 的 RPC 机制创建、配置和管理 OCF 缓存设备

- 提供了如 bdev_ocf_create、bdev_ocf_delete 等命令

1. ctx.c/h：

- 实现了 OCF 上下文（Context）

- 提供了 OCF 库所需的环境抽象

- 管理 OCF 实例的生命周期

1. volume.c/h：

- 封装了对底层存储卷的操作

- 在 OCF 和 SPDK bdev 之间提供了一个抽象层

1. data.c/h：

- 处理数据传输

- 实现了 OCF 和 SPDK 之间的数据移动

1. utils.c/h：

- 提供了各种辅助函数

- 包括日志、错误处理等功能

1. stats.c/h：

- 实现了统计信息的收集和报告

- 追踪缓存命中率、I/O 性能等指标

## SPDK、OCF 和 module/bdev/ocf 之间的关系

### 三者的层次结构

+----------------+
|      SPDK      |  SPDK 提供高性能存储框架和 bdev 抽象
+----------------+
        |
        | 通过 module/bdev/ocf 集成
        v
+---------------------+
| module/bdev/ocf|  适配层，将 OCF 缓存功能封装为 SPDK bdev
+---------------------+
        |
        | 使用 OCF 库的 API
        v
+----------------+
|      OCF       | OCF 提供块设备缓存算法和管理
+----------------+

### 具体关系说明

1. SPDK 与 module/bdev/ocf：

- SPDK 定义了块设备（bdev）接口规范

- module/bdev/ocf 实现了这些接口，使其成为 SPDK 中的一个标准块设备模块

- SPDK 调用 module/bdev/ocf 中实现的回调函数来处理 I/O 请求

- module/bdev/ocf 通过 SPDK 的 RPC 机制暴露管理接口

1. module/bdev/ocf 与 OCF：

- module/bdev/ocf 使用 OCF 库的 API 来创建和管理缓存实例

- 它将 SPDK 的异步 I/O 模型转换为 OCF 期望的模型

- 提供 OCF 所需的环境函数（内存分配、锁、线程等）

- 将 OCF 的回调转换回 SPDK 的回调机制

1. OCF 与 SPDK：

- 它们没有直接关系，完全通过 module/bdev/ocf 进行交互

- OCF 是一个独立的缓存库，不依赖于 SPDK

- SPDK 是一个存储性能开发套件，不直接依赖于 OCF

## 工作流程示例

当用户通过 SPDK 对一个 OCF 缓存设备发出读请求时，大致流程如下：

1. SPDK 接收用户请求，并路由到相应的 OCF bdev 设备

1. vbdev_ocf.c 中的 I/O 处理函数接收请求

1. 该函数将 SPDK bdev_io 转换为 OCF 请求格式

1. 通过 OCF API 提交请求到 OCF 缓存层

1. OCF 处理请求（检查缓存是否命中，管理缓存策略等）

1. OCF 调用 module/bdev/ocf 提供的回调函数读取数据（可能从缓存设备或核心设备）

1. module/bdev/ocf 将这些回调转换为 SPDK bdev I/O 操作

1. 数据返回给 OCF，然后返回给 module/bdev/ocf

1. module/bdev/ocf 完成原始的 SPDK 请求

1. SPDK 将结果返回给用户

当您添加预取功能时，您可能需要在这个流程中插入预取逻辑，例如在步骤 5 之后，根据访问模式决定是否触发预取操作。

## 总结

module/bdev/ocf 扮演了适配器的角色，它将通用的 OCF 缓存库与 SPDK 的高性能 I/O 框架连接起来。这种设计允许 SPDK 用户利用 OCF 的缓存功能，而不需要深入了解 OCF 的内部工作原理。同时，它也让 OCF 能够在不修改其核心代码的情况下，获得 SPDK 提供的高性能异步 I/O 能力。
