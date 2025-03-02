当使用 `hexo d` 命令之后，hexo 会将静态文件推送到 Github 的指定分支，进行自动化部署。

当需要对博客进行修改时，只需要对 source 文件夹中的源文件进行修改即可。为了保证在不同设备上编辑上传博客内容的一致性，我们需要在 Github 仓库的另外一个分支中维护 source 文件夹中的源文件。

## 编辑博客流程

首先需要拉取 Github 仓库 source 分支的内容，保证 source 内容的同步最新。

```bash
git clone -b source git@github.com:lingwu-hb/lingwu-hb.github.io.git
```

然后，在本地编辑博客内容，编辑完成后，将修改推送到 Github 仓库 source 分支。

```bash
git commit -a -m "update blog"
git push origin source:source
```

最后，使用 hexo d 将最新的静态文件推送到 Github 仓库的 main 分支，进行自动化部署即可。

```bash
hexo g # 生成静态文件
hexo d
```
