---
title: useful tools
date: 2025-06-11 11:18:27
categories:
- 随笔
tags:
- useful tools
---


# 配置 zsh && oh-my-zsh

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