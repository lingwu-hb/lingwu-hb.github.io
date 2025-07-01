---
title: useful tools
date: 2025-06-11 11:18:27
categories:
- 随笔
tags:
- useful tools
---

# 常用工具

## 配置 zsh && oh-my-zsh

1. ZSH（Z-Shell）是一种功能强大的 Unix shell，提供了许多增强功能，如高级脚本能力、自动补全和主题支持。

`sudo apt install zsh`

2. Oh-My-Zsh 是一个用于管理 ZSH 配置的流行框架，提供了丰富的主题和插件。使用以下命令安装

`sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"`

3. 插件安装

`git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting`


`git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions`

4. 插件启动，修改 ~/.zshrc 配置文件

```shell
plugins=(git
        zsh-autosuggestions
        zsh-syntax-highlighting
        pip
        sudo
        last-working-dir
        )
```



## 安装 conda

conda 是包和环境管理工具，能够很方便得拿到特定的环境，实现环境隔离。

安装流程如下：

1. Wget 下载

```bash
wget https://mirrors.bfsu.edu.cn/anaconda/archive/Anaconda3-2022.10-Linux-x86_64.sh --no-check-certificate
```

> :heavy_exclamation_mark: :heavy_exclamation_mark: :heavy_exclamation_mark:  如果出现报错信息：ERROR 403: Forbidden，需要加上 --user-agent=“Mozilla”

```bash
wget --user-agent="Mozilla" https://mirrors.bfsu.edu.cn/anaconda/archive/Anaconda3-2022.10-Linux-x86_
64.sh --no-check-certificate
```

2. 执行安装脚本

```bash
bash Anaconda3-2021.11-Linux-x86_64.sh
```

3. 写入配置文件

```bash
echo 'export PATH="/home/ubuntu/anaconda3/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

> :exclamation::exclamation::exclamation: 注意这里需要明确的路径，而不是 `~/anaconda3/bin:$PATH`

4. 执行 conda init [shell_name] 进行初始化

```bash
conda init zsh
```

conda 自带的脚本会执行一系列操作，完成初始配置。

## 文件上传与下载

1、从服务器上下载文件

```
scp username@servername:/path/filename /var/www/local_dir（本地目录）
```

 例如scp root@192.168.0.101:/var/www/test.txt  把192.168.0.101上的/var/www/test.txt 的文件下载到/var/www/local_dir（本地目录）

2、上传本地文件到服务器

```
scp /path/filename username@servername:/path   
```

例如scp /var/www/test.php  root@192.168.0.101:/var/www/  把本机/var/www/目录下的test.php文件上传到192.168.0.101这台服务器上的/var/www/目录中

 

3、从服务器下载整个目录

```
scp -r username@servername:/var/www/remote_dir/（远程目录） /var/www/local_dir（本地目录）
```

例如:scp -r root@192.168.0.101:/var/www/test  /var/www/  

4、上传目录到服务器

```
scp  -r local_dir username@servername:remote_dir
```

例如：scp -r test  root@192.168.0.101:/var/www/   把当前目录下的test目录上传到服务器的/var/www/ 目录



## Git 常用命令

### 分支相关

```bash
git checkout -b [new_branch] origin/[new_branch]
```

本地新建一个分支，并跟踪远端的分支，然后切换到该分支。



# 常见问题

## Include 报错

`CTRL + SHIFT + P` 打开 vscode 终端，搜索 JSON，选中 `C/C++: Edit Configurations(JSON)`
然后在 "includePath" 中增加需要 include 的路径（不同的库文件，路径不相同），对于 glib.h ，可以参考以下格式：

```shell
{
    "configurations": [
        {
            "name": "Linux",
            "includePath": [
                "${workspaceFolder}/**",
                "/usr/include/c++/9",
                "/usr/include/x86_64-linux-gnu/c++/9",
                "/usr/include/c++/9/backward",
                "/usr/lib/gcc/x86_64-linux-gnu/9/include",
                "/usr/local/include",
                "/usr/include/x86_64-linux-gnu",
                "/usr/include",
                "/usr/include/glib-2.0",
                "/usr/lib/x86_64-linux-gnu/glib-2.0/include"
            ],
            "defines": [],
            "compilerPath": "/usr/bin/gcc",
            "cStandard": "c17",
            "cppStandard": "c++98",
            "intelliSenseMode": "linux-gcc-x64"
        }
    ],
    "version": 4
}
```



## 云服务器 ssh 断连

ssh 服务的稳定需要占用一定的带宽和 IO，如果系统 CPU 和 IO 占用率过高，将会导致 ssh 超时而自动断开连接。

解决方案：

1. 提升 ssh cpu 占用优先级
2. 提升 ssh 带宽占用优先级
3. 修改 ssh 配置文件
4. 换用更轻量级的工具连接，cursor 工具增加了较多负载压力，可以直接换成 terminal 执行命令。

主要有以下几个思路，具体解决方案可以参考 AI 工具









