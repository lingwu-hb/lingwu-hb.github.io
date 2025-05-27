# Hexo Blog 部署指南

当使用 `hexo d` 命令之后，hexo 会将静态文件推送到 Github 的指定分支，进行自动化部署。

当需要对博客进行修改时，只需要对 `source` 文件夹中的源文件进行修改即可。为了保证在不同设备上编辑上传博客内容的一致性，我们需要在 Github 仓库的另外一个分支中维护 `source` 文件夹中的源文件。

## 编辑博客流程

### 1. 同步 source 分支文件

#### 旧设备同步流程 

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

#### 新设备同步流程

1. 拉取 Github 仓库 source 分支的内容，保证 source 内容的同步最新。
```bash
git clone -b source git@github.com:lingwu-hb/lingwu-hb.github.io.git
```

### 2. 编辑博客

在本地编辑博客内容：

```bash
hexo new "New Blog Name"
```

然后用 markdown 打开进行编辑。

编辑完成后，将修改推送到 Github 仓库 source 分支：

```bash
git commit -a -m "update blog"
git push origin source:source
```

### 3. 部署博客

#### 方式一：使用部署脚本（推荐）

我们提供了一个 Windows 批处理脚本 `deploy.bat` 来自动化部署流程。该脚本会依次执行以下操作：
1. 添加所有更改到 git
2. 提交更改（使用提供的提交信息）
3. 推送到 source 分支
4. 生成静态文件
5. 部署到 GitHub Pages

使用方法：
```bash
deploy.bat "你的提交信息"
```

例如：
```bash
deploy.bat "更新博客：添加新文章"
```

> ⚠️ 注意：如果任何步骤失败，脚本会立即停止并显示详细的错误信息。

#### 方式二：手动部署

如果你想手动执行部署步骤，可以使用以下命令：

```bash
hexo g # 生成静态文件
hexo d # 部署到远程仓库

hexo s # 本地预览
```
