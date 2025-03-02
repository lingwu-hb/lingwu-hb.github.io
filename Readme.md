当使用 `hexo d` 命令之后，hexo 会将静态文件推送到 Github 的指定分支，进行自动化部署。

当需要对博客进行修改时，只需要对 source 文件夹中的源文件进行修改即可。为了保证在不同设备上编辑上传博客内容的一致性，我们需要在 Github 仓库的另外一个分支中维护 source 文件夹中的源文件。

# 编辑博客流程

## 1. 同步 source 分支文件

### 旧设备同步流程 

1.1 首先拉取远端 source 分支的最新版本
```bash
git pull origin source:source
```
git pull 是 git fetch 和 git merge 的组合命令，会自动拉取远端的最新变更并合并到当前分支。

1.2 解决冲突（如果有）
如果本地分支和远端分支有冲突，Git 会提示你解决冲突。你需要手动编辑冲突的文件，选择保留的内容，然后标记冲突已解决：
```bash
git add <冲突文件>
git commit
```

1.3 强制覆盖本地分支（如果需要）
如果你希望完全覆盖本地分支，使其与远端分支完全一致，可以使用强制覆盖命令：
```bash
git fetch origin
git checkout main
git reset --hard origin/main
```
> 注意： 这会丢失本地分支的所有未提交的变更，请谨慎操作。

### 新设备同步流程

1.1 拉取 Github 仓库 source 分支的内容，保证 source 内容的同步最新。

```bash
git clone -b source git@github.com:lingwu-hb/lingwu-hb.github.io.git
```

## 2. 编辑博客

然后，在本地编辑博客内容，编辑完成后，将修改推送到 Github 仓库 source 分支。

```bash
git commit -a -m "update blog"
git push origin source:source
```

## 3. 部署博客

使用 hexo d 将最新的静态文件推送到 Github 仓库的 main 分支，进行自动化部署即可。

```bash
hexo g # 生成静态文件
hexo d
```
