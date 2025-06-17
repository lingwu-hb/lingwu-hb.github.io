---
title: attention mechanism
date: 2025-06-06 10:05:14
categories:
- AI
tags:
- Attention
---

# Transformer 的向量化与 Attention 机制解析

[参考视频](https://www.bilibili.com/video/BV1TZ421j7Ke/?spm_id_from=333.337.search-card.all.click&vd_source=dc1f57f4d0f3636b7a85bb3e052b778f)

## 向量化（Embedding）

向量化是将输入文本中的单词或子词（Token）转化为高维向量（Embedding）的过程。每个 Token 会被映射到一个高维空间中的向量，用于表示其语义信息。

在 Transformer 的原始论文中，Embedding 的维度通常设为 512：
$$
dim_emb = 512
$$

- **初始 Embedding**：相同的 Token（例如同一个单词）会被赋予相同的初始 Embedding 向量。
- **上下文调整**：由于同一个单词在不同句子或同一句子的不同位置可能具有不同含义，Transformer 通过后续的 Attention 机制和位置编码（Positional Encoding）调整每个 Token 的 Embedding，使其不仅表示单词本身，还能捕捉丰富的上下文信息。

**直观理解**：你可以将 Embedding 想象成一个高维空间中的“坐标点”，每个 Token 是一个点，而 Transformer 的任务是通过上下文调整这些点的“位置”，让它们更准确地反映语义。

------

## Attention 机制

Attention 机制是 Transformer 的核心，用于计算 Token 之间的相关性，并根据上下文调整 Embedding。核心公式如下：
$$
Attention(Q, K, V ) = softmax( QK^T / √d_k )V
$$

### Q、K、V 向量的生成

- Q（Query）与 K（Key）向量：
  $$ Q = W_kE $$
  $$ K = W_kE $$

  - 其中，$E$ 是输入的 Embedding 向量，维度为 $d_{emb}$（如 512）。
  - $W_q$ 和 $W_k$ 是可学习的权重矩阵，维度为 $d_k \times d_{emb}$，通常 $d_k < d_{emb}$，从而将 Embedding 映射到较低维度的空间。
  - $Q$ 和 $K$ 的点积（$QK^T$）计算了每个 Token 对其他 Token 的相关性。点积值越大，表示两个 Token 的语义关联越强。

- V（Value）向量：
  $$
  V = W_vE
  $$

  - $W_v$ 是另一个可学习的权重矩阵，维度同样为 $d_k \times d_{emb}$。
  - $V$ 表示 Token 的语义内容，经过 Attention 机制的加权后，生成新的上下文感知的向量表示。

- 归一化与加权：

  - $QK^T$ 计算得到相关性矩阵，经过 $\sqrt{d_k}$ 缩放（防止点积值过大导致 softmax 梯度消失）。
  - $\text{softmax}$ 将相关性矩阵归一化为 0 到 1 之间的权重，称为“注意力分数”。
  - 最后，注意力分数与 $V$ 相乘，得到加权后的输出，融合了上下文信息。

------

## 通俗理解

Attention 机制的本质是通过计算 Token 之间的相关性，动态调整每个 Token 的表示，使其包含上下文信息。我们可以简化公式来理解其核心思想：

参考文章：[Attention 机制解析](https://www.zhihu.com/question/298810062)

忽略权重矩阵 $W_q$、$W_k$、$W_v$ 和缩放因子，公式简化为：
$$
Attention(Q, K, V ) = softmax( QK^T / √d_k )V \approx QK^TV \approx W_qE(WkE)^TW_vE \approx EE^TE
$$

- **$E E^T$（注意力矩阵）**：表示每个 Token 与其他 Token 的相似度。相似度越高，说明两个 Token 越相关，分配的“注意力”越多。
- **$\text{softmax}(E E^T)$**：将相似度归一化为注意力分数，类似于概率分布。
- **乘以 $E$**：用注意力分数对原始 Embedding 进行加权平均，生成新的向量表示，融合了上下文信息。

**类比**：想象一群人在开会，每个人（Token）都在“听”其他人（通过 $E E^T$ 计算相关性），然后根据“听到的内容”（注意力分数）调整自己的发言（Embedding），最终形成更符合整体讨论的观点。

