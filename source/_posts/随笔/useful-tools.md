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

操作1：本地新建一个分支，并跟踪远端的分支，然后切换到该分支。

```bash
git checkout -b [new_branch] origin/[new_branch]
```

操作2：先拉取远端分支信息，然后检查当前分支相对于远端分支的具体情况。可用于判断本地分支是否落后于远端分支。


```bash
git fetch; git status
```

操作3：给当前分支修改名称

```bash
git branch -M <new_branch_name>
```

操作4：git commit 后，再修改 .gitignore 文件，让 .gitignore 文件生效。

```bash
git rm -r --cached <file-or-directory>
```
* `file-or-directory` 是你不想要继续跟踪的文件或目录路径。
* `--cached` 确保文件只从 `Git` 的索引中移除，本地文件不会被删除。

```bash
git commit --amend --no-edit
```
* 执行 `git rm -r --cached` 后，运行此命令会更新最近的提交，去掉不想要的文件。
* `--no-edit` 表示保留原提交信息，不需要修改。

然后再进行后续的提交操作即可。


### 远端仓库相关

操作1：添加/删除远程仓库关联到本地仓库

```bash
git remote add/remove <remote hub name> <remote hub url>
```

操作2：强制将本地仓库内容覆盖到远端仓库

```bash
git push --force origin main:main
```

### Tag 相关操作

操作1：从远程仓库拉取所有标签

```bash
git fetch --tags
```

操作2：列出本地标签，并附带详细信息

```bash
git tag -n
```

操作3：列出远程分支

```bash
git ls-remote --tags origin
```

操作4：显示特定标签的特定信息

```bash
git show <tag-name>
```

操作5：于标签所在的提交创建一个新分支

```bash
git checkout -b baseline v1.0
```




## vscode 常用插件配置

1. Material Theme

可以直接美化背景和代码高亮，非常好看

2. GitLens

经典的展示 git 提交历史的插件，也是非常好用

3. CMake

能使CMakeLists.txt的书写变得容易，具有自动补全和高亮功能。

# 常见问题

## Include 报错

`CTRL + SHIFT + P` 打开 vscode 终端，搜索 JSON，选中 `C/C++: Edit Configurations(JSON)` 然后在 "includePath" 中增加需要 include 的路径（不同的库文件，路径不相同），可以在命令行使用 `pkg-config --cflags <pkg-name>` 的方式获取对应包的编译路径。

对于 glib.h ，可以参考以下格式：

```shell
{
    "configurations": [
        {
            "name": "Linux",
            "includePath": [
                "${workspaceFolder}/**",
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

:exclamation:注意：

有时候配置文件中会出现一行： `"configurationProvider": "ms-vscode.makefile-tools"`，它告诉 VS Code 的 C/C++ 扩展：**不要用 c_cpp_properties.json 的配置**， 而是去问 **Makefile Tools 扩展**，让它来提供 includePath、defines 等。

因此，把这行删除即可。

## 云服务器 ssh 断连

ssh 服务的稳定需要占用一定的带宽和 IO，如果系统 CPU 和 IO 占用率过高，将会导致 ssh 超时而自动断开连接。

解决方案：

1. 提升 ssh cpu 占用优先级
2. 提升 ssh 带宽占用优先级
3. 修改 ssh 配置文件
4. 换用更轻量级的工具连接，cursor 工具增加了较多负载压力，可以直接换成 terminal 执行命令。

主要有以下几个思路，具体解决方案可以参考 AI 工具

## 如何从 Github 开源工具库下载工具

当你从 GitHub 的 **"Releases"** 页面下载工具时，你看到的“Assets”（附件）列表其实是一个矩阵，它由 `操作系统` x `CPU架构` x `打包方式` 组合而成。

开发者会提前将源代码“编译”成在特定平台上能直接运行的程序（称为“预编译版”或“二进制文件”），方便普通用户使用。

掌握下面这个“三步定位法”，你就能轻松找到你需要的那个文件。

### 第一步：锁定你的“操作系统” (OS)

首先，在文件名中寻找代表你操作系统的关键词。

- **Windows:** 寻找 `windows`、`win` 或文件后缀 `.exe`、`.msi`。
- **macOS:** 寻找 `macos`、`darwin` (macOS 的内核名) 或文件后缀 `.dmg`。
- **Linux:** 寻找 `linux` 或文件后缀 `.deb`、`.rpm`、`.AppImage`。

> **[以 Tabby 为例]** 你的系统是 Windows。所以我们立刻排除了所有包含 `linux` 和 `macos` 的文件。

### 第二步：匹配你的“CPU 架构” (Architecture)

这是最容易混淆的一步。它决定了软件是否能在你的电脑硬件上运行。

| **常见标识**    | **含义**    | **适配的电脑**                                               |
| --------------- | ----------- | ------------------------------------------------------------ |
| **`x64`**       | 64 位       | **绝大多数 Windows 电脑** 和 **Intel 芯片的 Mac**。          |
| `x86_64`        | 64 位       | `x64` 的另一种写法，完全相同。                               |
| `amd64`         | 64 位       | 还是 `x64` 的另一种写法 (因为 AMD 最早发明了 64 位扩展)。    |
| **`arm64`**     | 64 位 (ARM) | **苹果 M1/M2/M3 芯片的 Mac**、树莓派 (Raspberry Pi)、极少数 Windows (如 Surface Pro X)。 |
| `aarch64`       | 64 位 (ARM) | `arm64` 的另一种写法，完全相同。                             |
| `x86`           | 32 位       | 非常老的电脑 (2007 年以前)。几乎已被淘汰。                   |
| `i386` / `i686` | 32 位       | `x86` 的另一种写法。                                         |
| `armv7l`        | 32 位 (ARM) | 较老的 ARM 设备 (如旧版树莓派)。                             |

**如何选择？**

- 如果你用 Windows 电脑，99% 的情况选 **`x64`**。
- 如果你用 Apple Mac，看芯片：Intel 芯片选 `x64`，M 系列芯片选 **`arm64`**。

> **[以 Tabby 为例]** 你用 Windows 电脑，大概率是 `x64`。我们锁定了 `...-x64.exe` 和 `...-x64.zip`。而那些 `arm64` 和 `armv7l` 的文件就可以忽略了。

### 第三步：选择“打包方式” (Package Type)

你已经锁定了平台和架构，最后一步是选择你喜欢的“使用方式”。

#### 1. 安装版 (Installer)

- **特征：** 文件名常包含 `setup`、`install`，或后缀为 `.exe` / `.msi` (Windows), `.dmg` (macOS), `.deb` / `.rpm` (Linux)。
- **含义：** 这是一个标准的安装向导。它会帮你处理好一切，如创建快捷方式、设置环境变量、写入注册表等。
- **建议：** **初学者首选。**

#### 2. 便携版 (Portable / "绿色版")

- **特征：** 文件名常包含 `portable`，或后缀为 `.zip`、`.tar.gz`、`.AppImage`。
- **含义：** 这是一个压缩包，解压后即可运行，无需安装。所有配置都会保存在它自己的文件夹里。
- **建议：** 适合高级用户、想在 U 盘上使用或不希望“污染”系统的人。

#### 3. 源代码 (Source Code)

- **特征：** `Source code (zip)` 或 `Source code (tar.gz)`。
- **含义：** 这是程序的“图纸”（代码原文）。
- **建议：** **普通用户绝对不要下载这个！** 这是给开发者用来编译或研究代码的。

### 实战总结：以 Tabby 为例

我们来完整地走一遍你的案例：

1. **系统是 Windows？** -> 排除 `linux` 和 `macos`。
2. **CPU 是 x64？** (大概率是) -> 排除 `arm64` 和 `armv7l`。
3. **想要安装版还是便携版？**
   - **安装版 (推荐):** `tabby-1.0.229-setup-x64.exe`
   - **便携版 (备选):** `tabby-1.0.229-portable-x64.zip`

### 附：快速在 GitHub 找到下载页面

你问的另一个问题是“如何方便快速地下载”。所有“编译好”的工具都存放在一个标准位置：

1. 打开一个开源项目的 GitHub 首页 (例如 `github.com/Eugeny/tabby`)。
2. 在页面的**右侧边栏**，寻找 **"Releases"** (发行版) 模块。
3. 点击 "Releases" 标题或“Latest” (最新) 标签。
4. 这就进入了你看到的下载页。展开 **"Assets"** (附件) 列表，就可以看到所有文件了。







