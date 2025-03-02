---
title: OS Lab
date: 2024-07-05 13:36:57
categories:
- system
tags:
- OS Lab
---





操作系统实验分为四个部分：中断相关、内存系统、进程系统、文件系统

## 实验一：trap

### 中断的概念及其具体过程

当发生一个中断，假设其目标模式（即执行中断例程的模式）为机器模式，RISC-V处理器硬件将执行以下动作：

1）保存（进入中断处理历程之前的）pc（如果是trap或者interrupt，则保存下一条指令的pc）到mepc寄存器；

2）将（进入中断处理历程之前的）特权级保存到mstatus寄存器的MPP字段；

3）将mstatus寄存器中的MIE字段保存到（它自己的）MPIE字段；

4）设置mcause，其值与表1.6中的Interrupt和Exception code对应；

5）将pc设置为中断例程的入口，如果为直接模式则设置为mtvec的值；

6）将mstatus寄存器的MIE字段清零，转入机器模式。

后续，会由软件按照pc指定的中断例程的入口执行中断处理程序。包括对通用寄存器的保护、对进程堆栈的保护等。

* 中断过程中软件的实现如下：

```assembly
smode_trap_vector:
    # swap a0 and sscratch, so that points a0 to the trapframe of current process
    csrrw a0, sscratch, a0
    // 交换后sscratch指向中断例程入口，a0指向当前用户进程入口

    # save the context (user registers) of current process in its trapframe.
    addi t6, a0 , 0

    # store_all_registers is a macro defined in util/load_store.S, it stores contents
    # of all general purpose registers into a piece of memory started from [t6].
    store_all_registers
    // 将用户进程相关信息保存到t6指向的地址空间，后面需要修改a0寄存器

    # come back to save a0 register before entering trap handling in trapframe
    # [t0]=[sscratch]
    csrr t0, sscratch
    sd t0, 72(a0)

    # use the "user kernel" stack (whose pointer stored in p->trapframe->kernel_sp)
    ld sp, 248(a0)

    # load the address of smode_trap_handler() from p->trapframe->kernel_trap
    ld t0, 256(a0)

    # jump to smode_trap_handler() that is defined in kernel/trap.c
    jr t0
```

上述汇编代码，完成了对通用寄存器和堆栈的保护。

### 程序执行中内存布局及相关寄存器

一个可执行文件在静态和处于运行态时，其组织的结构完全不同。下面以ELF（The Executable and Linking Format）格式的文件为例，讨论两者具体区别。

* 静态时组织结构

对于ELF文件而言，分为链接视图 + 执行视图

![elf.png](https://s2.loli.net/2024/07/06/jwfbK2VM6gSmhLT.png)

在本实验中，主要需要使用ELF文件的执行视图，也就是分为代码段、堆栈段、静态数据段等segment。

进程在执行的时候，需要对函数调用栈进行回溯。子程序在被调用时，堆栈上会保留子程序的地址（详细内容见后面处于运行态的结构介绍）。根据子程序的地址，可以在代码段中找到对应函数的执行位置，进而找到该函数的名称，从而打印出函数名。

* 运行态内存结构

主要需要捋清楚fp(s0)、ra和sp三个寄存器的作用。

fp(s0)：当前函数栈帧的栈底

ra：当前函数执行完毕之后的返回地址

sp：当前函数栈帧的栈顶

![fig1_2.png](https://s2.loli.net/2024/07/06/mwMdYJauiLbDX9h.png)

所以在执行代码时，打印完当前函数的名称后，需要跳转到上一层函数，按照上述栈帧内容对三个寄存器按照下面方式进行调整即可：

```c
user_sp = user_s0;
user_s0 = *(uint64*)(user_s0-16);
user_ra = *(uint64*)(user_s0-8);
```



## 实验二：内存系统

主要内容：

1. 熟悉通过虚拟地址找到物理地址的流程

通过页目录和多级页表进行查找即可。（简单设计，不考虑脏页等情况）

2. pke系统下，虚拟地址空间和物理地址空间各个段的对应分布情况

![user_address_mapping.png](https://s2.loli.net/2024/07/06/kFHUT5Z2PwiCLmE.png)



## 实验三：进程系统

主要内容：

1. 进程的调度相关

pke系统中，简单设置一个静态进程池，用于保存所有可用的进程。

```c
process procs[NPROC];

void init_proc_pool() {
  memset( procs, 0, sizeof(process)*NPROC );

  for (int i = 0; i < NPROC; ++i) {
    procs[i].status = FREE;
    procs[i].pid = i;
  }
}
```

进程调度层面，直接设置就绪队列、阻塞队列，然后依次将就绪队列中进程上处理机执行即可。

2. fork子进程，父子进程之间内存的关系

fork出来的子进程，其代码段和堆栈段和父进程相同，只有数据段是相对独立的。

与实验四中的挑战实验二不同，实验四的挑战实验二实现了一个简易的shell进程，其可以fork一个子进程，载入一个新的可执行文件，然后进行执行。

## 实验四：文件系统

文件系统一般来说提供以下功能：读写文件、文件安全保障、为应用程序提供合理的内存空间。

那我们要完成的文件系统实验，大概率就是需要补全用户应用程序在进行文件访问时，所遇到的问题。

一句话，文件系统是操作系统中负责管理持久化数据的子系统。

所谓元数据，可以理解为用户存储的数据结构化信息的数据。

也就是说，磁盘中对磁盘信息进行管理的数据，一般来说都被称为元数据。

VFS的目的为支持多种文件系统工作。通过对访问路径的识别，VFS可以判断文件具体交给了哪个系统进行管理。

进程会使用文件，多个进程会使用同一个文件，多个文件也可能被同一个进程所使用。所以，需要对文件的使用情况进行检测。

我们知道，每个进程块都有一个结构体，用来保存该进程所打开文件的具体信息；那么对应到具体文件，其是否需要保存打开该文件的进程信息呢？

**先整理一下进程保存了文件的哪些信息**

```cpp
// data structure that manages all openned files in a PCB
typedef struct proc_file_management_t {
    struct dentry *cwd;  // vfs dentry of current working directory
    struct file opened_files[MAX_FILES];  // opened files array
    int nfiles;  // the number of opened files a process has
} proc_file_management;
```



看了一下，这个实验中，文件对应的数据结构并没有存储其被哪些进程打开。但是成熟的文件系统都会进行保存。

在Linux中，可以查看文件被哪些进程所使用，但是似乎也并不简单。



不同的I/O模式下，read操作的流程不完全相同。

为什么操作系统文件I/O需要先将数据读取到内核缓冲区,再拷贝到进程缓冲区？

1. 性能上能够通过内核的一些IO策略进行优化（比如延迟写、预读等操作）
2. 安全上能够通过内核的检查保障各种情况（例如多进程读取同一文件）下的文件安全

在调用read系统调用的时候，需要传递用户空间的地址信息，所以内核知道应用程序的缓冲区地址，因此可以方便将数据从内核缓冲区写入到进程缓冲区。



关于各种文件I/O模式的区分

文件I/O：进程通过内核对磁盘中的文件进行操作的过程。

区分依据

1. 根据是否使用标准库提供的缓冲：缓冲I/O和非缓冲I/O
2. 根据是否使用操作系统提供的缓冲：直接I/O和非直接I/O

I/O的过程分为两步：数据的准备 + 将数据从内核缓冲区转入到进程缓冲区

阻塞I/O会在第一步就进行阻塞等待；而非阻塞I/O在操作系统完成第一步之前不断轮询，直到操作系统完成第一步操作，通过中断通知进程读取数据。

前面提到的所有I/O模式都需要在I/O过程完成前等待，都属于同步I/O；而异步I/O不需要等待这两步操作，进程不会停止等待，而是不断执行。等内核执行完所有操作后再告知进程即可。



VFS和其他文件系统一样，也会在内存中建立一个目录树结构。任何文件系统的目录树都需要先挂载在这颗文件树上才能使用。

VFS系统中通过dentry结构对目录进行组织。所谓的挂载，其实也就是相当于将实际的磁盘中的目录树挂载到一个新的内存中的虚拟目录树的某一个节点上，从而便于后续系统进行路径的访问操作。



vinode和文件是一一对应的关系。dentry中最关键的成员就是name，以及该dentry对应的文件的vinode，表示为dentry_inode。在硬链接情况下，会存在不同的dentry中的dentry_inode相同的情况。



整体上介绍了整个文件系统的组成情况：如何对文件系统进行挂载、RFS和VFS中几个重要的数据结构以及其各自的作用。



可以对同一个文件按照既读又写的方式打开两边嘛？

同一个进程内，是可以同时多次打开同一个文件的。这些打开文件符之间，文件偏移是互相独立的，其他内容都是彼此关联的：例如内存中只存在一份动态文件，所有的文件描述符中的inode节点都指向同一个文件。



在完成一个项目的过程中，我的目的究竟到底是什么呢？是仅仅完成项目任务吗？不！大学四年，我完成了挺多的项目任务，但是为什么总感觉什么都没有学会呢？我认为我缺乏思考，我应该思考一些有意义的问题，然后从解决这些问题中习得方法才行。



RFS系统创建一个文件的步骤

1. 在内存中找到一个空闲的空间存储dinode节点
2. 初始化dinode数据结构（本质就是初始化新文件的信息 + 为新文件腾出空间）
3. 将初始化完成的dinode结构体写入到对应的文件系统磁盘中
4. 根据盘号信息初始化vinode结构体（重点是vinode->inum，表明了该文件所在的位置）
5. 维护RFS系统中的文件树（将该文件作为parent节点的子树节点）



通过文件系统的实验，我明白了操作系统中**文件系统的构成和工作原理**



### 打开文件

- 进程层

- - 将打开的文件file，加入到current->pfiles->opened_files中

- VFS层

- - 不同文件系统的共同打开文件的抽象

- RFS层

- - 涉及到具体的文件系统中的各自的数据结构的维护操作

这种分层的思想，本质上也属于设计模式中的分层思想。



### 文件系统挑战实验

#### 挑战实验1

实现pwd和cd函数、完成对相对路径的解析

Q：操作系统中能否在应用程序中拿到进程的当前工作路径呢？如果能拿到，思考程序是否应该拿到，已经是否应该使用一个多余的变量维护进程的工作路径？

真实的pwd命令会调用cwd系统调用获取工作路径，但是系统中也存在CWD这一环境变量，用来保存系统的工作路径。某些时候，pwd命令会简单打印CWD。

或许可以通过在进程中维护一个全局变量，在执行后续的命令的时候，直接通过prasePath对传入的路径字符串进行解析，然后对正确的路径进行访问即可。

需要考虑两个方面：

1. 实现cd命令

主要就是修改CWD这一个全局变量即可，后续执行pwd命令的时候，直接输出即可。

1. 对于其他的所有需要使用相对路径进行访问的系统调用



捋清楚数组名类型和字符指针类型之前的区别和联系！

重点搞清楚在哪些使用情况下，这两种类型会有显著区别！

1. 相似点

首先，它们都是char*类型，可以传递给需要char*类型的函数

1. 区别

字符指针就是一个普通的指针变量；而数组名就是一个别名，系统分配了一片连续的地址空间，然后将首地址永久得和数组名绑定起来。数组名本身并不会占用内存空间，而字符指针由于其本质上就是一个变量，所有需要占用内存中四个字节的空间。



实验文档中指名可能需要修改RFS内部的部分文件，但是是否真的需要呢？

后续学习了设计模式之后，可能能够再回头回顾这部分内容，了解真实地操作系统是如何实现的。



很多诸如此类的功能，其实现方法往往都是多种多样的，但是一般来说，设计模式都会指导出一种相对最优解。

在后续看Ceph源码的时候，需要重点思考如果不这样设计，会引发哪些问题？从而能够对成熟的框架设计形成自己的更深层次的理解。



#### 挑战实验2

实现一个简单的Shell进程，该进程能够读取一个可执行文件，进程进而执行可执行文件代码！该部分涉及到更换进程的代码段和数据段

exec函数用来在一个进程中启动另一个程序执行。其中可执行文件通过文件的路径名指定，从文件系统中读出。exec会根据读入的可执行文件将原进程的数据段、代码段和堆栈段替换。

参考lab3_challenge1完成即可。



学习了解进程结构体的内容组成

```c
// the extremely simple definition of process, used for beginning labs of PKE
typedef struct process_t {
    // pointing to the stack used in trap handling.
    uint64 kstack;
    // user page table
    pagetable_t pagetable;
    // trapframe storing the context of a (User mode) process.
    trapframe* trapframe;

    // points to a page that contains mapped_regions. below are added @lab3_1
    mapped_region *mapped_info;
    // next free mapped region in mapped_info
    int total_mapped_region;

    // process id
    uint64 pid;
    // process status
    int status;
    // parent process
    struct process_t *parent;
    // next queue element
    struct process_t *queue_next;

    // accounting. added @lab3_3
    int tick_count;
}process;
```

其中部分内容涉及到中断的处理，中断的过程，首先是内核对部分寄存器进行保存，然后陷入到内核中。操作系统需要完成用户进程现场的保存工作，然后通过中断向量表跳转到中断处理例程，执行中断处理，最后中断返回，需要恢复现场（包括硬件和软件共同执行，硬件恢复PC等寄存器，软件恢复其他通用寄存器等。）



父进程想要通过exec命令执行另外的一个可执行文件，主要需要完成以下工作：

在挑战实验3_1中，需要实现fork功能创建一个子进程。对于子进程而言，其code_seg和父进程相同、数据段独立、堆栈段拷贝、上下文共享！

而对于挑战实验4_1中，exec执行的另外一个可执行文件中，启动的子进程中，所有的段都与父进程不同。
