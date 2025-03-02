---
title: C语言宏定义通过成员变量获取类指针最优解
date: 2025-02-23 23:16:25
categories:
- system
tags:
- c语言
- 宏定义
---

# 问题简介

最近在看开源 OCF 源码的时候，发现了一个 C 语言宏定义的常见使用技巧。从初见的不解，到了解之后的惊叹，不得不感叹于底层开发人员关于性能的极致追求！

在编程开发中，经常需要进行变量之间的类型转换操作。一个类` A` 中存在类型为`B `的成员变量。假设现在我拥有一个类型为` B` 的变量` v1`，我需要得到一个类型为` A` 的变量 `v2`，同时 `v2->B `就为变量` v1`。

# 方法一

一般来说，对于此类问题，熟悉 C++ 的初学者会考虑采用以下的方法实现： 

```cpp
// 用宏定义实现此功能！
#define CONVERT_B_TO_A(v1) A(v1)

class B {
    // B 类的定义
};
class A {
public:
    B b;
    A(const B& b_val) : b(b_val) {}
};
int main() {
    B v1;
    A v2 = CONVERT_B_TO_A(v1);  // 使用宏进行转换
    return 0;
}
```

 但是这种方法需要使用到 c++ 的构造函数，同时会产生额外的内存拷贝。

# 方法二

类似的，c 语言也可以采用这种方法实现，只需要模拟实现 c++ 中的构造函数即可。

代码如下：

```cpp
// 假设 B 是一个简单的结构体
typedef struct {
    int value;
} B;
// 结构体 A 包含一个 B 类型的成员
typedef struct {
    int other_member;
    B b;
} A;
// 宏定义：将 B 类型的变量 v1 转换为 A 类型的变量 v2
#define CONVERT_B_TO_A(v1) \
    ({ \
        A temp; \
        memset(&temp, 0, sizeof(A)); \
        temp.b = v1; \
        temp; \
    })
int main() {
    B v1 = {42}; // 初始化 B 类型的变量 v1
    A v2 = CONVERT_B_TO_A(v1); // 使用宏将 v1 转换为 A 类型的变量 v2

    printf("v2.b.value = %d\n", v2.b.value); // 输出: v2.b.value = 42
    return 0;

}
```

c 语言的写法稍显繁琐，但是本质上和 c++ 完全相同。并且通过 c 语言的写法，我们能够更容易得发现这种方法的弊端，在宏定义中进行了一次多余的内存拷贝操作。

# 方法三

在底层开发中，这种功能性的宏定义会被调用得非常频繁，因此系统开发者们会追求极致的性能，性能最优的代码如下：

```cpp
#define container_of(ptr, type, member) ({          \
    const typeof(((type *)0)->member)*__mptr = (ptr);    \
    (type *)((char *)__mptr - offsetof(type, member)); })
```

解析如下：

------

`const typeof(((type *)0)->member)*__mptr = (ptr);`

* `((type *)0)：`

将 0 强制转换为 `type*` 类型的指针。这里 0 是一个空指针，表示一个假设的` type `结构体的起始地址。

这种写法不会真正访问内存，只是为了在编译时获取类型信息。

* `((type *)0)->member：`

访问假设的 `type` 结构体中的 `member` 成员。

例如，如果 `type` 是` A`，`member` 是` b`，那么 `((A *)0)->b`就是` B `类型的成员。

* `typeof(((type *)0)->member)：`

使用` typeof` 关键字获取` member `成员的类型。

例如，如果` member` 是`B `类型，那么 `typeof(((A *)0)->b) `就是` B`。

* `const typeof(((type *)0)->member)*__mptr = (ptr);：`

定义一个指向 `member` 类型的指针 `__mptr`，并将其初始化为传入的 `ptr`。

这里使用 `const` 是为了防止意外修改 `__mptr` 指向的内容。

例如，如果 `ptr` 是 `B* `类型，那么 `__mptr` 也是` B* `类型。

------

`(type *)((char *)__mptr - offsetof(type, member));`

* `offsetof(type, member)：`

使用` offsetof `宏计算 `member` 在` type `结构体中的偏移量。

`offsetof` 的实现通常是编译器内置的，它会返回 `member `相对于结构体起始地址的字节偏移量。

例如，如果 `member` 是 `b`，且` b` 在 `A `结构体中的偏移量是 4 字节，那么 `offsetof(A, b) `返回 4。

* `(char *)__mptr：`

将 `__mptr `强制转换为` char* `类型。`char*` 是一个字节指针，方便进行指针算术运算。

因为指针算术的单位是指针指向的类型的大小，而` char` 的大小是 1 字节，所以将指针转换为` char*` 后，加减操作的单位就是字节。

* `(char *)__mptr - offsetof(type, member)：`

将` __mptr `的地址减去 `member` 在结构体中的偏移量，得到结构体的起始地址。

例如，如果 `mptr` 指向` b`，且` b` 的偏移量是 4 字节，那么` (char *)mptr - 4 `就是 `A `结构体的起始地址。

* `(type *)：`

将计算出的地址强制转换为 `type*` 类型，即结构体的指针。

例如，如果 `type` 是 `A`，那么最终返回的就是 `A* `类型的指针。

# 总结

`container_of` 宏的原理可以概括为以下几步：

通过 `typeof` 获取成员的类型，并定义一个临时指针` __mptr` 指向传入的成员指针。

使用 `offsetof` 计算成员在结构体中的偏移量。

将成员指针转换为 `char*` 类型，减去偏移量，得到结构体的起始地址。

将起始地址强制转换为结构体指针类型。

`container_of` 可以使用直接通过指针运算获取结构体地址，无需额外的内存拷贝。适用于任何结构体和成员类型。
