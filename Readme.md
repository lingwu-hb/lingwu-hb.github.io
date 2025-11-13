# Hexo Blog 部署指南

当使用 `hexo d` 命令之后，hexo 会将静态文件推送到 Github 的指定分支，进行自动化部署。

当需要对博客进行修改时，只需要对 `source` 文件夹中的源文件进行修改即可。为了保证在不同设备上编辑上传博客内容的一致性，我们需要在 Github 仓库的另外一个分支中维护 `source` 文件夹中的源文件。

## 1 项目介绍

这是一个基于 [Hexo](https://hexo.io/) 框架搭建的个人博客项目。Hexo 是一个快速、简洁且高效的静态博客框架，使用 Markdown 解析文章，可以快速生成静态网页并部署到 GitHub Pages 等平台。

### 1.1 项目结构

```
.
├── .deploy_git/          # 部署相关文件
├── .git/                 # Git 版本控制文件
├── .github/              # GitHub 相关配置
├── .vscode/              # VS Code 配置
├── node_modules/         # 依赖包
├── public/               # 生成的静态文件
├── scaffolds/            # 模板文件夹
├── source/               # 源文件
│   ├── _posts/           # 博客文章
│   ├── _posts_organized/ # 分类整理的文章
│   ├── categories/       # 分类页面
│   ├── css/              # 自定义 CSS
│   ├── img/              # 图片资源
│   └── tags/             # 标签页面
├── themes/               # 主题文件
├── _config.yml           # 站点配置文件
├── _config.landscape.yml # 主题配置文件
├── deploy.bat            # 部署脚本
├── package.json          # 项目依赖配置
├── Readme.md             # 项目说明文档
└── update_links.py       # 更新链接脚本
```

### 1.2 技术栈

- **框架**：Hexo 静态博客框架
- **主题**：Butterfly
- **部署**：GitHub Pages
- **版本控制**：Git (双分支策略)
  - `main` 分支：存放生成的静态文件
  - `source` 分支：存放博客源文件

### 1.3 工作流程

本项目采用双分支策略进行版本控制和部署：
1. 在 `source` 分支上维护博客的源文件
2. 通过 Hexo 将源文件生成为静态文件
3. 将静态文件部署到 `main` 分支
4. GitHub Pages 自动从 `main` 分支获取静态文件并展示

## 2 编辑博客流程

### 2.0 新电脑配置相关环境

需要 `git & node` 工具，然后通过 `node` 安装 `hexo-cli` 工具即可。

> 具体可以在浏览器搜一下 hexo 相关教程即可

### 2.1 同步 source 分支文件

#### 2.1.1 旧设备同步流程 

1. 首先拉取远端 source 分支的最新版本
```bash
git pull origin source:source
```
> git pull 是 git fetch 和 git merge 的组合命令，会自动拉取远端的最新变更并合并到当前分支。

2. 解决冲突（如果有）
如果本地分支和远端分支有冲突，Git 会提示你解决冲突。你需要手动编辑冲突的文件，选择保留的内容，然后标记冲突已解决：
```bash
git add <冲突文件>
git commit
```

3. 强制覆盖本地分支（如果需要）
如果你希望完全覆盖本地分支，使其与远端分支完全一致，可以使用强制覆盖命令：
```bash
git fetch origin
git checkout main
git reset --hard origin/main
```
> ⚠️ 注意：这会丢失本地分支的所有未提交的变更，请谨慎操作。

#### 2.1.2 新设备同步流程

1. 拉取 Github 仓库 source 分支的内容，保证 source 内容的同步最新。
```bash
git clone -b source git@github.com:lingwu-hb/lingwu-hb.github.io.git
```

### 2.2 编辑博客

在本地编辑博客内容：

```bash
hexo new "New Blog Name"
```

然后用 markdown 打开进行编辑。

#### 2.2.1 图片处理

当博客需要使用图片时，需要执行以下流程：

1. 将图片防止到 source/img/ 文件下
2. 直接将图片拖入到 md 文件中，进行预览编辑
3. 博客编辑完之后，**手动将所有图片的路径修改成 /img/test.png 格式**，方便 hexo 进行渲染

### 2.3 部署博客

#### 2.3.1 方式一：使用部署脚本（推荐）

我们提供了一个 Windows 批处理脚本 `deploy.bat` 来自动化部署流程。该脚本会依次执行以下操作：
1. 执行 update_links 脚本，生成副本文件夹
2. 添加所有更改到 git
3. 提交更改（使用提供的提交信息）
4. 推送到 source 分支
5. 生成静态文件
6. 部署到 GitHub Pages

使用方法：
```bash
deploy.bat "你的提交信息"
```

例如：
```bash
deploy.bat "更新博客：添加新文章"
```

> ⚠️ 注意：如果任何步骤失败，脚本会立即停止并显示详细的错误信息。

#### 2.3.2 方式二：手动部署

如果你想手动执行部署步骤，可以使用以下命令：

```bash
python update_links.py
git add .
git commit -m "info"
git push origin source:source
hexo g # 生成静态文件
hexo d # 部署到远程仓库
hexo s # 本地预览
```
